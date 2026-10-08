"""Simple command-line workflow for reviewing a legal PDF with Foundry agents."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pypdf import PdfReader

from rag.local_retrieval import retrieve_requirements

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "contracts" / "sample-vendor-agreement.pdf"
DEFAULT_OUTPUT = ROOT / "memory" / "latest-review.json"
KNOWLEDGE_DIR = ROOT / "data" / "knowledge_base"
DISCLAIMER = (
    "This is an AI-assisted preliminary document review. Final legal decisions "
    "must be made by an authorized legal professional."
)


class WorkflowError(RuntimeError):
    """Raised when a workflow step cannot produce a valid result."""


@dataclass(frozen=True)
class Settings:
    project_endpoint: str
    clause_agent_name: str
    compliance_agent_name: str
    embedding_model: str

    @classmethod
    def from_environment(cls) -> Settings:
        load_dotenv(ROOT / ".env")
        values = {
            "project_endpoint": os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT", ""),
            "clause_agent_name": os.getenv(
                "CLAUSE_EXTRACTION_AGENT_NAME", "clause-extraction-agent"
            ),
            "compliance_agent_name": os.getenv(
                "COMPLIANCE_VALIDATION_AGENT_NAME", "compliance-validation-agent-sk"
            ),
            "embedding_model": os.getenv(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"
            ),
        }
        missing = [name for name, value in values.items() if not value.strip()]
        if missing:
            variable_names = {
                "project_endpoint": "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT",
                "clause_agent_name": "CLAUSE_EXTRACTION_AGENT_NAME",
                "compliance_agent_name": "COMPLIANCE_VALIDATION_AGENT_NAME",
                "embedding_model": "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            }
            required = ", ".join(variable_names[name] for name in missing)
            raise WorkflowError(f"Missing required environment variables: {required}")
        return cls(**values)


def extract_pdf(pdf_path: Path) -> dict[str, Any]:
    """Extract text page by page from a PDF."""
    if not pdf_path.is_file():
        raise WorkflowError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise WorkflowError(f"Expected a PDF file, received: {pdf_path.name}")

    try:
        reader = PdfReader(pdf_path)
    except Exception as exc:
        raise WorkflowError(f"Could not open PDF '{pdf_path.name}': {exc}") from exc

    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:
            raise WorkflowError(
                f"Could not extract page {page_number} from '{pdf_path.name}': {exc}"
            ) from exc
        pages.append({"page_number": page_number, "text": text})

    if not any(page["text"] for page in pages):
        raise WorkflowError(
            "The PDF contains no extractable text. Scanned PDFs require OCR, which "
            "is outside this simple workflow."
        )

    return {
        "file_name": pdf_path.name,
        "number_of_pages": len(pages),
        "extraction_status": "success",
        "pages": pages,
    }


def parse_json_response(raw_text: str, step_name: str) -> dict[str, Any]:
    """Parse an agent response that must contain one JSON object."""
    text = raw_text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WorkflowError(
            f"{step_name} returned invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(value, dict):
        raise WorkflowError(f"{step_name} must return a JSON object.")
    return value


def invoke_agent(
    project_client: AIProjectClient,
    agent_name: str,
    prompt: str,
    step_name: str,
) -> dict[str, Any]:
    """Invoke the latest version of an existing Foundry prompt agent."""
    try:
        with project_client.get_openai_client(agent_name=agent_name) as openai_client:
            response = openai_client.responses.create(input=prompt)
    except Exception as exc:
        raise WorkflowError(
            f"{step_name} failed while invoking Foundry agent '{agent_name}': {exc}"
        ) from exc

    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise WorkflowError(f"{step_name} returned no text output.")
    return parse_json_response(output_text, step_name)


def build_clause_prompt(document: dict[str, Any]) -> str:
    return (
        "Extract the required legal clauses from this locally extracted PDF. "
        "Follow your configured instructions and return only the required JSON. "
        "Preserve exact contract evidence and page numbers. Do not invent evidence.\n\n"
        f"DOCUMENT:\n{json.dumps(document, ensure_ascii=False)}"
    )


def build_compliance_prompt(
    file_name: str,
    clause_result: dict[str, Any],
    retrieved_requirements: list[dict[str, Any]],
) -> str:
    return (
        "Review these extracted clauses for compliance using ONLY the locally retrieved "
        "policy passages supplied below. Do not call or rely on an attached knowledge "
        "base. Follow your configured output instructions and return only the required "
        "JSON. Cite source_document exactly as supplied. If the supplied passages do not "
        "support a finding, use 'Insufficient evidence' rather than inventing a source.\n\n"
        f"DOCUMENT NAME: {file_name}\n"
        f"CLAUSE RESULT:\n{json.dumps(clause_result, ensure_ascii=False)}\n\n"
        "RETRIEVED POLICY PASSAGES:\n"
        f"{json.dumps(retrieved_requirements, ensure_ascii=False)}"
    )


def validate_clause_result(result: dict[str, Any]) -> None:
    if not isinstance(result.get("clauses"), list):
        raise WorkflowError(
            "Clause Extraction Agent response must contain a 'clauses' list."
        )


def validate_compliance_result(result: dict[str, Any]) -> None:
    if not isinstance(result.get("findings"), list):
        raise WorkflowError(
            "Compliance Validation Agent response must contain a 'findings' list."
        )


def run_workflow(
    pdf_path: Path,
    output_path: Path,
    settings: Settings,
) -> dict[str, Any]:
    document = extract_pdf(pdf_path)

    with (
        DefaultAzureCredential(
            exclude_interactive_browser_credential=False
        ) as credential,
        AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=credential,
        ) as project_client,
    ):
        clauses = invoke_agent(
            project_client,
            settings.clause_agent_name,
            build_clause_prompt(document),
            "Clause extraction",
        )
        validate_clause_result(clauses)

        with project_client.get_openai_client() as openai_client:
            retrieved_requirements = retrieve_requirements(
                openai_client=openai_client,
                embedding_model=settings.embedding_model,
                clauses=clauses["clauses"],
                knowledge_dir=KNOWLEDGE_DIR,
            )

        compliance = invoke_agent(
            project_client,
            settings.compliance_agent_name,
            build_compliance_prompt(
                document["file_name"], clauses, retrieved_requirements
            ),
            "Compliance validation",
        )
        validate_compliance_result(compliance)

    report = {
        "document": {
            "file_name": document["file_name"],
            "number_of_pages": document["number_of_pages"],
            "extraction_status": document["extraction_status"],
        },
        "clauses": clauses["clauses"],
        "retrieved_requirements": retrieved_requirements,
        "compliance_findings": compliance["findings"],
        "disclaimer": DISCLAIMER,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a legal PDF locally, invoke the existing Foundry Clause "
            "Extraction and Compliance Validation agents, and save a JSON report."
        )
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"PDF to review (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSON report path (default: {DEFAULT_OUTPUT})",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        settings = Settings.from_environment()
        report = run_workflow(args.pdf.resolve(), args.output.resolve(), settings)
    except WorkflowError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Reviewed: {report['document']['file_name']}")
    print(f"Clauses: {len(report['clauses'])}")
    print(f"Compliance findings: {len(report['compliance_findings'])}")
    print(f"Report saved to: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
