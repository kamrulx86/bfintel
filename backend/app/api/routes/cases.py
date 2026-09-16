import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.case import Case, CaseNote
from app.schemas.soc import CaseCreate, CaseNoteCreate, CaseNoteOut, CaseOut, CaseUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[CaseOut])
def list_cases(db: DbSession, user: CurrentUser, status: str | None = Query(default=None)) -> list[CaseOut]:
    q = select(Case).where(Case.organization_id == user.organization_id)
    if status:
        q = q.where(Case.status == status)
    rows = db.scalars(q.order_by(Case.updated_at.desc()).limit(200)).all()
    return [CaseOut.model_validate(r) for r in rows]


@router.post("", response_model=CaseOut)
def create_case(db: DbSession, user: CurrentUser, body: CaseCreate) -> CaseOut:
    row = Case(
        organization_id=user.organization_id,
        title=body.title,
        severity=body.severity,
        priority=body.priority,
        source_ip=body.source_ip,
        attack_session_id=body.attack_session_id,
        created_by=user.id,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="case.create", target=body.title)
    db.commit()
    db.refresh(row)
    return CaseOut.model_validate(row)


@router.get("/{case_id}", response_model=CaseOut)
def get_case(db: DbSession, user: CurrentUser, case_id: uuid.UUID) -> CaseOut:
    row = db.scalar(select(Case).where(Case.id == case_id, Case.organization_id == user.organization_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseOut.model_validate(row)


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(db: DbSession, user: CurrentUser, case_id: uuid.UUID, body: CaseUpdate) -> CaseOut:
    row = db.scalar(select(Case).where(Case.id == case_id, Case.organization_id == user.organization_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    for field in ("status", "assignee", "severity", "priority"):
        val = getattr(body, field)
        if val is not None:
            setattr(row, field, val)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="case.update", target=str(case_id))
    db.commit()
    db.refresh(row)
    return CaseOut.model_validate(row)


@router.get("/{case_id}/notes", response_model=list[CaseNoteOut])
def list_notes(db: DbSession, user: CurrentUser, case_id: uuid.UUID) -> list[CaseNoteOut]:
    case = db.scalar(select(Case).where(Case.id == case_id, Case.organization_id == user.organization_id))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    rows = db.scalars(select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.created_at.desc())).all()
    return [CaseNoteOut.model_validate(r) for r in rows]


@router.post("/{case_id}/notes", response_model=CaseNoteOut)
def add_note(db: DbSession, user: CurrentUser, case_id: uuid.UUID, body: CaseNoteCreate) -> CaseNoteOut:
    case = db.scalar(select(Case).where(Case.id == case_id, Case.organization_id == user.organization_id))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    note = CaseNote(case_id=case_id, author_id=user.id, body=body.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return CaseNoteOut.model_validate(note)
