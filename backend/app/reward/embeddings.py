"""Embedding generation for findings using sentence-transformers."""
from __future__ import annotations
import numpy as np
from functools import lru_cache
from app.models.findings import Finding
from app.config import get_settings


@lru_cache(maxsize=1)
def _get_embedding_model():
    """Lazy-load the sentence transformer model."""
    from sentence_transformers import SentenceTransformer
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def generate_finding_embedding(finding: Finding) -> np.ndarray:
    """Generate an embedding vector for a finding."""
    model = _get_embedding_model()
    
    # Combine relevant text fields for a rich embedding
    text = _finding_to_text(finding)
    embedding = model.encode(text, convert_to_numpy=True)
    
    return embedding


def generate_text_embedding(text: str) -> np.ndarray:
    """Generate embedding for arbitrary text."""
    model = _get_embedding_model()
    return model.encode(text, convert_to_numpy=True)


def generate_batch_embeddings(findings: list[Finding]) -> list[np.ndarray]:
    """Generate embeddings for multiple findings (batched for efficiency)."""
    model = _get_embedding_model()
    texts = [_finding_to_text(f) for f in findings]
    embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
    return list(embeddings)


def _finding_to_text(finding: Finding) -> str:
    """Convert a finding to a text representation for embedding."""
    parts = [
        f"Category: {finding.category.value}",
        f"Title: {finding.title}",
        f"Description: {finding.description}",
        f"Severity: {finding.severity.value}",
    ]
    if finding.rule_violated:
        parts.append(f"Rule: {finding.rule_violated}")
    if finding.evidence:
        code_snippets = " | ".join(e.code_snippet for e in finding.evidence if e.code_snippet)
        if code_snippets:
            parts.append(f"Code: {code_snippets}")
    
    return " | ".join(parts)
