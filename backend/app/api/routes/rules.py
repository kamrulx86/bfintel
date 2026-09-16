import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.automation_rule import AutomationRule
from app.models.rule_execution import RuleExecution
from app.models.user import Role
from app.schemas.automation import RuleCreate, RuleExecutionOut, RuleOut
from app.services.audit import write_audit
from app.services.rules_engine import evaluate_rules

router = APIRouter(prefix="/rules", tags=["rules"])


def _require_admin(user: CurrentUser) -> None:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Admin only")


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
