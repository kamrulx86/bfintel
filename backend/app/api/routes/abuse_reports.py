import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.abuse_report import AbuseReport
from app.models.user import Role
from app.schemas.abuse_report import AbuseReportCreate, AbuseReportFromIpRequest, AbuseReportOut, AbuseReportUpdate
from app.services.abuse_report_builder import build_brute_force_report
from app.services.audit import write_audit
from app.services.ip_investigation import get_ip_profile

router = APIRouter(prefix="/abuse-reports", tags=["abuse-reports"])


@router.get("", response_model=list[AbuseReportOut])
def list_reports(
    db: DbSession,
    user: CurrentUser,
    status: str | None = Query(default=None),
    source_ip: str | None = Query(default=None),
) -> list[AbuseReportOut]:
    q = select(AbuseReport).where(AbuseReport.organization_id == user.organization_id)
    if status:
        q = q.where(AbuseReport.status == status)
    if source_ip:
        q = q.where(AbuseReport.source_ip == source_ip)
    rows = db.scalars(q.order_by(AbuseReport.updated_at.desc()).limit(200)).all()
    return [AbuseReportOut.model_validate(r) for r in rows]


@router.post("", response_model=AbuseReportOut)
def create_report(db: DbSession, user: CurrentUser, body: AbuseReportCreate) -> AbuseReportOut:
    row = AbuseReport(
        organization_id=user.organization_id,
        source_ip=body.source_ip.strip(),
        case_id=body.case_id,
        subject=body.subject,
        body=body.body,
        recipient_email=body.recipient_email,
        isp_name=body.isp_name,
        asn=body.asn,
        template_key=body.template_key,
        created_by=user.id,
    )
    db.add(row)
    write_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="abuse_report.create",
        target=body.source_ip,
    )
    db.commit()
    db.refresh(row)
    return AbuseReportOut.model_validate(row)


@router.post("/from-ip/{source_ip}", response_model=AbuseReportOut)
def create_from_ip(
    db: DbSession,
    user: CurrentUser,
    source_ip: str,
    body: AbuseReportFromIpRequest | None = None,
) -> AbuseReportOut:
    ip = source_ip.strip()
    profile = get_ip_profile(db, user.organization_id, ip)
    if not profile:
        raise HTTPException(status_code=404, detail="No investigation data for this IP")

    template = (body.template_key if body else "brute_force") or "brute_force"
    if template != "brute_force":
        raise HTTPException(status_code=400, detail="Unsupported template")

    subject, text, isp, asn = build_brute_force_report(profile)
    row = AbuseReport(
        organization_id=user.organization_id,
        source_ip=ip,
        case_id=body.case_id if body else None,
        subject=subject,
        body=text,
        isp_name=isp,
        asn=asn,
        template_key=template,
        created_by=user.id,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="abuse_report.draft", target=ip)
    db.commit()
    db.refresh(row)
    return AbuseReportOut.model_validate(row)


@router.get("/{report_id}", response_model=AbuseReportOut)
def get_report(db: DbSession, user: CurrentUser, report_id: uuid.UUID) -> AbuseReportOut:
    row = db.scalar(
        select(AbuseReport).where(AbuseReport.id == report_id, AbuseReport.organization_id == user.organization_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return AbuseReportOut.model_validate(row)


@router.patch("/{report_id}", response_model=AbuseReportOut)
def update_report(
    db: DbSession,
    user: CurrentUser,
    report_id: uuid.UUID,
    body: AbuseReportUpdate,
) -> AbuseReportOut:
    row = db.scalar(
        select(AbuseReport).where(AbuseReport.id == report_id, AbuseReport.organization_id == user.organization_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    for field in ("status", "subject", "body", "recipient_email"):
        val = getattr(body, field)
        if val is not None:
            setattr(row, field, val)
    write_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="abuse_report.update",
        target=str(report_id),
    )
    db.commit()
    db.refresh(row)
    return AbuseReportOut.model_validate(row)


@router.post("/{report_id}/submit", response_model=AbuseReportOut)
def mark_submitted(db: DbSession, user: CurrentUser, report_id: uuid.UUID) -> AbuseReportOut:
    if user.role not in (Role.admin.value, Role.analyst.value):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = db.scalar(
        select(AbuseReport).where(AbuseReport.id == report_id, AbuseReport.organization_id == user.organization_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    row.status = "submitted"
    row.submitted_at = datetime.now(timezone.utc)
    write_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="abuse_report.submit",
        target=row.source_ip,
    )
    db.commit()
    db.refresh(row)
    return AbuseReportOut.model_validate(row)
