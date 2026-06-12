"""Feature engineering for the reward model classifier."""
from __future__ import annotations
import numpy as np
from app.models.findings import Finding, FindingCategory, Severity
from app.reward.embeddings import generate_finding_embedding


# Category one-hot encoding order
CATEGORIES = [
    FindingCategory.BOUNDED_CONTEXT,
    FindingCategory.LAYER_VIOLATION,
    FindingCategory.SECURITY_BOUNDARY,
    FindingCategory.COMMUNICATION_PATTERN,
    FindingCategory.DEPENDENCY_RULE,
    FindingCategory.PRINCIPLE_VIOLATION,
]

# Severity one-hot encoding order
SEVERITIES = [
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.ADVISORY,
]


def compute_features(finding: Finding) -> np.ndarray:
    """Compute the full feature vector for a finding.
    
    Feature vector composition:
    - [0:384] text embedding (semantic meaning)
    - [384:390] category one-hot (6 dims)
    - [390:395] severity one-hot (5 dims)
    - [395] evidence count (normalized)
    - [396] total evidence text length (normalized)
    - [397] has rule reference (binary)
    - [398] has context reference (binary)
    - [399] confidence from defender (if available)
    
    Total: 400 dimensions
    """
    # Text embedding (384 dims)
    embedding = generate_finding_embedding(finding)
    
    # Category one-hot (6 dims)
    category_vec = np.zeros(len(CATEGORIES))
    try:
        idx = CATEGORIES.index(finding.category)
        category_vec[idx] = 1.0
    except ValueError:
        pass
    
    # Severity one-hot (5 dims)
    severity_vec = np.zeros(len(SEVERITIES))
    try:
        idx = SEVERITIES.index(finding.severity)
        severity_vec[idx] = 1.0
    except ValueError:
        pass
    
    # Structured features
    evidence_count = min(len(finding.evidence) / 5.0, 1.0)  # Normalize to 0-1
    evidence_length = min(
        sum(len(e.code_snippet) for e in finding.evidence) / 500.0, 1.0
    )
    has_rule = 1.0 if finding.rule_violated else 0.0
    has_context = 1.0 if finding.context_violated else 0.0
    confidence = finding.confidence
    
    # Concatenate all features
    structured = np.array([
        evidence_count,
        evidence_length,
        has_rule,
        has_context,
        confidence,
    ])
    
    feature_vector = np.concatenate([
        embedding,
        category_vec,
        severity_vec,
        structured,
    ])
    
    return feature_vector


def compute_batch_features(findings: list[Finding]) -> np.ndarray:
    """Compute features for multiple findings."""
    return np.array([compute_features(f) for f in findings])
