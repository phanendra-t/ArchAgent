"""Reward Model Scorer — scores findings and applies confidence filtering."""
from __future__ import annotations
from app.models.findings import Finding
from app.reward.model import get_reward_model
from app.reward.features import compute_features
from app.feedback.store import get_annotation_count
from app.config import get_settings


async def score_findings(
    findings: list[Finding],
) -> tuple[list[Finding], list[Finding], bool]:
    """Score findings with the reward model and filter by confidence.
    
    Returns:
        (visible_findings, suppressed_findings, reward_model_active)
    """
    settings = get_settings()
    
    # Check if reward model should be active
    count = await get_annotation_count()
    reward_model = get_reward_model()
    
    if count < settings.cold_start_threshold or not reward_model.is_available():
        # Cold start — return all findings unfiltered
        return findings, [], False
    
    # Score each finding
    visible = []
    suppressed = []
    
    for finding in findings:
        features = compute_features(finding)
        score = reward_model.predict(features)
        
        # Update finding with reward score
        finding = finding.model_copy()
        finding.reward_score = score
        
        if score >= settings.confidence_high:
            finding.confidence = score
            finding.suppressed = False
            visible.append(finding)
        elif score >= settings.confidence_low:
            finding.confidence = score
            finding.suppressed = False
            visible.append(finding)  # Show with "uncertain" badge
        else:
            finding.confidence = score
            finding.suppressed = True
            suppressed.append(finding)
    
    return visible, suppressed, True
