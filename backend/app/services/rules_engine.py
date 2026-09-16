import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret
from app.models.attack_session import AttackSession
from app.models.automation_rule import AutomationRule
from app.models.notification_channel import NotificationChannel
from app.models.notification_delivery import NotificationDelivery
from app.models.rule_execution import RuleExecution
from app.models.source_ip_intel import SourceIpIntel
from app.integrations.notifications.sender import send_to_channel
from app.services.allowlist import is_ip_allowlisted
from app.services.audit import write_audit
from app.services.notifications.templates import render_alert

from app.services.rule_conditions import match_conditions


def _session_context(db: Session, org_id: UUID, session: AttackSession) -> dict:
    intel = db.scalar(
        select(SourceIpIntel).where(
            SourceIpIntel.organization_id == org_id,
            SourceIpIntel.source_ip == session.source_ip,
        )
    )
    return {
        "risk_score": session.risk_score,
        "risk_level": session.risk_level,
        "attempt_count": session.attempt_count,
        "status": session.status,
        "attack_type": session.attack_type,
        "service": (session.services or [""])[0] if session.services else "",
        "country_code": intel.country_code if intel else None,
        "country_name": intel.country_name if intel else None,
    }


def _cooldown_active(db: Session, rule: AutomationRule, session_id: UUID) -> bool:
    since = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)
    exists = db.scalar(
        select(func.count())
        .select_from(RuleExecution)
        .where(
            RuleExecution.rule_id == rule.id,
            RuleExecution.attack_session_id == session_id,
            RuleExecution.created_at >= since,
        )
    )
    return bool(exists)


def evaluate_rules(db: Session, organization_id: UUID, *, dashboard_url: str = "") -> dict[str, int]:
    stats = {"rules": 0, "triggered": 0, "notifications": 0, "errors": 0}
    rules = db.scalars(
        select(AutomationRule).where(
            AutomationRule.organization_id == organization_id,
            AutomationRule.enabled.is_(True),
        )
    ).all()
    if not rules:
        return stats

    sessions = db.scalars(
        select(AttackSession)
        .where(AttackSession.organization_id == organization_id, AttackSession.status == "active")
        .order_by(AttackSession.last_seen.desc())
        .limit(200)
    ).all()

    for rule in rules:
        stats["rules"] += 1
        for session in sessions:
            if is_ip_allowlisted(db, organization_id, session.source_ip):
                continue
            ctx = _session_context(db, organization_id, session)
            if not match_conditions(ctx, rule.conditions):
                continue
            if _cooldown_active(db, rule, session.id):
                continue

            execution = RuleExecution(
                organization_id=organization_id,
                rule_id=rule.id,
                attack_session_id=session.id,
                source_ip=session.source_ip,
                context=ctx,
            )
            db.add(execution)
            db.flush()

            message = render_alert(
                session,
                country=ctx.get("country_name"),
                dashboard_url=dashboard_url,
            )
            action_errors: list[str] = []
            for action in rule.actions or []:
                if action.get("type") != "notify":
                    continue
                channel_id = action.get("channel_id")
                if not channel_id:
                    continue
                try:
                    cid = UUID(str(channel_id))
                except ValueError:
                    action_errors.append("invalid channel_id")
                    continue
                channel = db.scalar(
                    select(NotificationChannel).where(
                        NotificationChannel.id == cid,
                        NotificationChannel.organization_id == organization_id,
                        NotificationChannel.is_active.is_(True),
                    )
                )
                if not channel:
                    action_errors.append("channel not found")
                    continue
                config = json.loads(decrypt_secret(channel.config_enc))
                ok, err = send_to_channel(channel, config, message)
                delivery = NotificationDelivery(
                    organization_id=organization_id,
                    channel_id=channel.id,
                    rule_execution_id=execution.id,
                    status="sent" if ok else "failed",
                    payload={"text_preview": message[:500]},
                    error_message=err,
                    sent_at=datetime.now(timezone.utc) if ok else None,
                )
                db.add(delivery)
                stats["notifications"] += 1
                if not ok:
                    stats["errors"] += 1
                    action_errors.append(err or "send failed")

            execution.result = "success" if not action_errors else "partial"
            execution.detail = "; ".join(action_errors) if action_errors else "notifications dispatched"
            rule.last_triggered_at = datetime.now(timezone.utc)
            stats["triggered"] += 1

            write_audit(
                db,
                organization_id=organization_id,
                action="rule.executed",
                target=str(rule.id),
                result=execution.result,
                metadata={"source_ip": session.source_ip, "rule": rule.name},
            )
    return stats
