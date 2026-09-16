from app.core.correlation_config import CorrelationSettings


def compute_risk_score(
    attempt_count: int,
    successful_count: int,
    target_count: int,
    service_count: int,
    settings: CorrelationSettings,
) -> tuple[int, str]:
    score = 0
    if attempt_count >= settings.attempt_threshold:
        score += 25
    if attempt_count >= settings.attempt_threshold * 2:
        score += 20
    if target_count > 1:
        score += 15
    if service_count > 1:
        score += 10
    if successful_count > 0:
        score += 25
    if attempt_count >= settings.attempt_threshold * 5:
        score += 15

    score = min(100, score)
    if score >= 80:
        level = "critical"
    elif score >= 60:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"
    return score, level
