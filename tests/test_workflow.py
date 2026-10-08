from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from orchestration.workflow import (
    WorkflowError,
    extract_pdf,
    parse_json_response,
    validate_clause_result,
    validate_compliance_result,
)
from rag import local_retrieval
from rag.local_retrieval import (
    PolicyChunk,
    chunk_text,
    cosine_similarity,
    load_policy_chunks,
    retrieve_requirements,
)

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PDF = ROOT / "data" / "contracts" / "sample-vendor-agreement.pdf"
KNOWLEDGE_DIR = ROOT / "data" / "knowledge_base"


class FakeEmbeddings:
    def create(self, *, model: str, input: list[str]) -> Any:
        del model
        data = []
        for index, text in enumerate(input):
            vector = [1.0, 0.0] if "privacy" in text.lower() else [0.0, 1.0]
            data.append(SimpleNamespace(index=index, embedding=vector))
        return SimpleNamespace(data=data)


class FakeOpenAIClient:
    embeddings = FakeEmbeddings()


def test_extract_pdf_preserves_page_numbers() -> None:
    result = extract_pdf(SAMPLE_PDF)

    assert result["file_name"] == "sample-vendor-agreement.pdf"
    assert result["number_of_pages"] >= 1
    assert result["extraction_status"] == "success"
    assert result["pages"][0]["page_number"] == 1
    assert "Vendor Services Agreement" in result["pages"][0]["text"]


def test_parse_json_response_accepts_json_fence() -> None:
    result = parse_json_response('```json\n{"clauses": []}\n```', "test")

    assert result == {"clauses": []}


def test_parse_json_response_rejects_non_json() -> None:
    with pytest.raises(WorkflowError, match="returned invalid JSON"):
        parse_json_response("not json", "test")


def test_validate_clause_result_requires_list() -> None:
    with pytest.raises(WorkflowError, match="'clauses' list"):
        validate_clause_result({"clauses": "invalid"})


def test_validate_compliance_result_requires_list() -> None:
    with pytest.raises(WorkflowError, match="'findings' list"):
        validate_compliance_result({})


def test_chunk_text_respects_limit_and_overlap() -> None:
    chunks = chunk_text("one two three four five six", max_chars=13, overlap_chars=5)

    assert chunks == ["one two three", "three four", "four five six"]


def test_load_policy_chunks_reads_five_sources() -> None:
    chunks = load_policy_chunks(KNOWLEDGE_DIR)

    assert {chunk.source_document for chunk in chunks} == {
        "approved-contract-template.pdf",
        "data-privacy-requirements.pdf",
        "information-security-policy.pdf",
        "legal-compliance-guidelines.pdf",
        "vendor-contract-policy.pdf",
    }


def test_cosine_similarity_ranks_equal_vectors_highest() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_retrieve_requirements_returns_grounded_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        local_retrieval,
        "load_policy_chunks",
        lambda _: [
            PolicyChunk("privacy.pdf", 1, "Privacy retention requirements"),
            PolicyChunk("security.pdf", 2, "Security encryption requirements"),
        ],
    )

    results = retrieve_requirements(
        openai_client=FakeOpenAIClient(),
        embedding_model="embedding-model",
        clauses=[
            {
                "clause_name": "Data privacy",
                "status": "present",
                "contract_text": "Personal data",
                "explanation": "Vague privacy terms",
            }
        ],
        knowledge_dir=KNOWLEDGE_DIR,
        top_k=1,
    )

    assert results[0]["clause_name"] == "Data privacy"
    assert results[0]["passages"][0]["source_document"] == "privacy.pdf"
