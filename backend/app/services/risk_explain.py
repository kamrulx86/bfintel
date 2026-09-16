from app.core.correlation_config import CorrelationSettings, get_correlation_settings
from app.models.attack_session import AttackSession


def explain_attack_session(session: AttackSession, settings: CorrelationSettings | None = None) -> list[str]:
    settings = settings or get_correlation_settings()
    reasons: list[str] = []

    if session.attempt_count >= settings.attempt_threshold:
        reasons.append(f"+ High authentication-failure volume ({session.attempt_count} failures)")
    if session.target_count > 1:
        reasons.append(f"+ Multiple hosts targeted ({session.target_count})")
    if len(session.services or []) > 1:
        reasons.append(f"+ Multiple services targeted ({len(session.services or [])})")
    if session.successful_attempt_count > 0:
        reasons.append(f"+ Successful authentication observed ({session.successful_attempt_count})")
    if session.average_rate and session.average_rate >= settings.attempt_threshold / 2:
        reasons.append(f"+ Elevated attack velocity ({session.average_rate:.1f} attempts/min)")

    return reasons
