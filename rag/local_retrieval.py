"""Local PDF chunking and embedding-based retrieval."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pypdf import PdfReader


class EmbeddingsClient(Protocol):
    embeddings: Any


@dataclass(frozen=True)
class PolicyChunk:
    source_document: str
    page_number: int
    text: str


def chunk_text(text: str, max_chars: int = 1200, overlap_chars: int = 150) -> list[str]:
    """Split text at word boundaries with a small character overlap."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be between 0 and max_chars")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start
        size = 0
        while end < len(words):
            word_size = len(words[end]) + (1 if end > start else 0)
            if end > start and size + word_size > max_chars:
                break
            size += word_size
            end += 1

        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break

        overlap_size = 0
        next_start = end
        while next_start > start:
            candidate_size = len(words[next_start - 1]) + (
                1 if overlap_size else 0
            )
            if overlap_size + candidate_size > overlap_chars:
                break
            overlap_size += candidate_size
            next_start -= 1
        start = next_start if next_start > start else end

    return chunks


def load_policy_chunks(knowledge_dir: Path) -> list[PolicyChunk]:
    """Read every PDF in the local knowledge directory into source-aware chunks."""
    if not knowledge_dir.is_dir():
        raise FileNotFoundError(f"Knowledge directory not found: {knowledge_dir}")

    chunks: list[PolicyChunk] = []
    pdf_paths = sorted(knowledge_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {knowledge_dir}")

    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            for text in chunk_text(page_text):
                chunks.append(
                    PolicyChunk(
                        source_document=pdf_path.name,
                        page_number=page_number,
                        text=text,
                    )
                )

    if not chunks:
        raise ValueError("The knowledge-base PDFs contain no extractable text.")
    return chunks


def embed_texts(
    openai_client: EmbeddingsClient,
    model: str,
    texts: list[str],
) -> list[list[float]]:
    """Create embeddings in one request and preserve input order."""
    response = openai_client.embeddings.create(model=model, input=texts)
    ordered = sorted(response.data, key=lambda item: item.index)
    return [list(item.embedding) for item in ordered]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have equal dimensions.")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )


def build_clause_query(clause: dict[str, Any]) -> str:
    parts = [
        str(clause.get("clause_name", "")),
        str(clause.get("status", "")),
        str(clause.get("contract_text", "")),
        str(clause.get("explanation", "")),
    ]
    return " | ".join(part for part in parts if part)


def retrieve_requirements(
    openai_client: EmbeddingsClient,
    embedding_model: str,
    clauses: list[dict[str, Any]],
    knowledge_dir: Path,
    top_k: int = 2,
) -> list[dict[str, Any]]:
    """Return the most similar local policy passages for each clause."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    chunks = load_policy_chunks(knowledge_dir)
    queries = [build_clause_query(clause) for clause in clauses]
    if any(not query for query in queries):
        raise ValueError("Every clause must contain searchable content.")

    texts = [chunk.text for chunk in chunks] + queries
    vectors = embed_texts(openai_client, embedding_model, texts)
    chunk_vectors = vectors[: len(chunks)]
    query_vectors = vectors[len(chunks) :]

    retrievals: list[dict[str, Any]] = []
    for clause, query_vector in zip(clauses, query_vectors, strict=True):
        scored = sorted(
            (
                (cosine_similarity(query_vector, chunk_vector), chunk)
                for chunk, chunk_vector in zip(chunks, chunk_vectors, strict=True)
            ),
            key=lambda item: item[0],
            reverse=True,
        )[:top_k]
        retrievals.append(
            {
                "clause_name": clause.get("clause_name", ""),
                "passages": [
                    {
                        "source_document": chunk.source_document,
                        "page_number": chunk.page_number,
                        "text": chunk.text,
                        "similarity_score": round(score, 6),
                    }
                    for score, chunk in scored
                ],
            }
        )
    return retrievals
