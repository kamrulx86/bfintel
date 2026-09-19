import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.automation_rule import AutomationRule
from app.models.rule_execution import RuleExecution
from app.models.user import Role
from app.models.notification_channel import NotificationChannel
from app.schemas.automation import RuleCreate, RuleExecutionOut, RuleFromTemplateCreate, RuleOut, RuleTemplateOut
from app.services.audit import write_audit
from app.services.rule_templates import RULE_TEMPLATES, get_template
from app.services.rules_engine import evaluate_rules

router = APIRouter(prefix="/rules", tags=["rules"])


def _require_admin(user: CurrentUser) -> None:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/templates", response_model=list[RuleTemplateOut])
def list_rule_templates(_user: CurrentUser) -> list[RuleTemplateOut]:
    return [RuleTemplateOut.model_validate(t) for t in RULE_TEMPLATES]


@router.post("/from-template", response_model=RuleOut)
def create_rule_from_template(
    db: DbSession,
    user: CurrentUser,
    body: RuleFromTemplateCreate,
) -> RuleOut:
    _require_admin(user)
    tpl = get_template(body.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Unknown rule template")

    actions: list[dict] = []
    if body.channel_id:
        channel = db.scalar(
            select(NotificationChannel).where(
                NotificationChannel.id == body.channel_id,
                NotificationChannel.organization_id == user.organization_id,
            )
        )
        if not channel:
            raise HTTPException(status_code=404, detail="Notification channel not found")
        actions = [{"type": "notify", "channel_id": str(channel.id)}]

    name = (body.name_override or tpl["name"]).strip()
    row = AutomationRule(
        organization_id=user.organization_id,
        name=name,
        enabled=body.enabled,
        conditions=tpl["conditions"],
        actions=actions,
        cooldown_minutes=tpl["cooldown_minutes"],
    )
    db.add(row)
    write_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="rule.create_from_template",
        target=name,
        metadata={"template_id": body.template_id, "channel_id": str(body.channel_id) if body.channel_id else None},
    )
    db.commit()
    db.refresh(row)
    return RuleOut.model_validate(row)


@router.get("", response_model=list[RuleOut])
def list_rules(db: DbSession, user: CurrentUser) -> list[RuleOut]:
    rows = db.scalars(
        select(AutomationRule)
        .where(AutomationRule.organization_id == user.organization_id)
        .order_by(AutomationRule.created_at.desc())
    ).all()
    return [RuleOut.model_validate(r) for r in rows]


@router.post("", response_model=RuleOut)
def create_rule(db: DbSession, user: CurrentUser, body: RuleCreate) -> RuleOut:
    _require_admin(user)
    row = AutomationRule(
        organization_id=user.organization_id,
        name=body.name,
        enabled=body.enabled,
        conditions=body.conditions,
        actions=body.actions,
        cooldown_minutes=body.cooldown_minutes,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="rule.create", target=body.name)
    db.commit()
    db.refresh(row)
    return RuleOut.model_validate(row)


@router.patch("/{rule_id}/toggle", response_model=RuleOut)
def toggle_rule(db: DbSession, user: CurrentUser, rule_id: uuid.UUID) -> RuleOut:
    _require_admin(user)
    row = db.scalar(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.organization_id == user.organization_id,
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    row.enabled = not row.enabled
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="rule.toggle", target=str(rule_id))
    db.commit()
    db.refresh(row)
    return RuleOut.model_validate(row)


@router.get("/executions", response_model=list[RuleExecutionOut])
def list_executions(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[RuleExecutionOut]:
    rows = db.scalars(
        select(RuleExecution)
        .where(RuleExecution.organization_id == user.organization_id)
        .order_by(RuleExecution.created_at.desc())
        .limit(limit)
    ).all()
    return [RuleExecutionOut.model_validate(r) for r in rows]


@router.post("/evaluate")
def run_evaluate(db: DbSession, user: CurrentUser) -> dict:
    _require_admin(user)
    stats = evaluate_rules(db, user.organization_id)
    db.commit()
    return {"status": "ok", **stats}
