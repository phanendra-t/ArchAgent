"""Reward model trainer — retrain from accumulated annotations."""
from __future__ import annotations
import numpy as np
from app.reward.model import get_reward_model
from app.reward.embeddings import generate_text_embedding
from app.feedback.store import get_all_annotations
from app.config import get_settings


async def retrain_model() -> dict:
    """Retrain the reward model from all stored annotations."""
    annotations = await get_all_annotations()
    
    if not annotations:
        raise ValueError("No annotations available for training")
    
    settings = get_settings()
    if len(annotations) < settings.cold_start_threshold:
        raise ValueError(
            f"Need at least {settings.cold_start_threshold} annotations. "
            f"Currently have {len(annotations)}."
        )
    
    # Build training data
    X = []
    y = []
    
    for ann in annotations:
        # Generate embedding from stored finding text
        embedding = generate_text_embedding(ann["finding_text"])
        
        # Build feature vector (simplified — using embedding + category/severity encoding)
        category_vec = _encode_category(ann.get("finding_category", ""))
        severity_vec = _encode_severity(ann.get("finding_severity", ""))
        
        # Structured features
        structured = np.array([
            0.5,  # evidence count placeholder
            0.5,  # evidence length placeholder
            1.0 if ann.get("rule_violated") else 0.0,
            1.0 if ann.get("context_violated") else 0.0,
            1.0,  # defender confidence placeholder
        ])
        
        feature_vector = np.concatenate([embedding, category_vec, severity_vec, structured])
        X.append(feature_vector)
        
        # Label: 1 = valid, 0 = false_positive, 0.5 weight for partial
        label = ann["label"]
        if label == "valid":
            y.append(1)
        elif label == "false_positive":
            y.append(0)
        else:  # partial
            y.append(1)  # Treat as positive but with lower confidence
    
    X = np.array(X)
    y = np.array(y)
    
    # Train the model
    reward_model = get_reward_model()
    metrics = reward_model.train(X, y)
    
    return metrics


def _encode_category(category: str) -> np.ndarray:
    """One-hot encode finding category."""
    categories = [
        "bounded_context_violation",
        "layer_violation",
        "security_boundary_violation",
        "communication_pattern_violation",
        "dependency_rule_violation",
        "principle_violation",
    ]
    vec = np.zeros(6)
    if category in categories:
        vec[categories.index(category)] = 1.0
    return vec


def _encode_severity(severity: str) -> np.ndarray:
    """One-hot encode severity."""
    severities = ["critical", "high", "medium", "low", "advisory"]
    vec = np.zeros(5)
    if severity in severities:
        vec[severities.index(severity)] = 1.0
    return vec
