from app.models.attack_session import AttackSession


def render_alert(session: AttackSession, *, country: str | None = None, dashboard_url: str = "") -> str:
    hosts = ", ".join((session.target_hosts or [])[:3]) or "—"
    services = ", ".join(session.services or []) or "—"
    lines = [
        "HIGH RISK BRUTE-FORCE ALERT",
        "",
        f"Source: {session.source_ip}",
        f"Country: {country or 'Unknown'}",
        f"Attempts: {session.attempt_count}",
        f"Successful logins: {session.successful_attempt_count}",
        f"Targets: {hosts}",
        f"Services: {services}",
        f"Risk: {session.risk_score} / 100 ({session.risk_level})",
        f"First seen: {session.first_seen.isoformat()}",
        f"Last seen: {session.last_seen.isoformat()}",
    ]
    if dashboard_url:
        lines.extend(["", f"Dashboard: {dashboard_url}"])
    return "\n".join(lines)
