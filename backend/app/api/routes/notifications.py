import json
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.notification_channel import NotificationChannel
from app.models.user import Role
from app.schemas.automation import ChannelCreate, ChannelOut
from app.integrations.notifications.sender import send_to_channel
from app.services.audit import write_audit

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _require_admin(user: CurrentUser) -> None:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/channels", response_model=list[ChannelOut])
def list_channels(db: DbSession, user: CurrentUser) -> list[ChannelOut]:
    rows = db.scalars(
        select(NotificationChannel)
        .where(NotificationChannel.organization_id == user.organization_id)
        .order_by(NotificationChannel.created_at.desc())
    ).all()
    return [ChannelOut.model_validate(r) for r in rows]


@router.post("/channels", response_model=ChannelOut)
def create_channel(db: DbSession, user: CurrentUser, body: ChannelCreate) -> ChannelOut:
    _require_admin(user)
    row = NotificationChannel(
        organization_id=user.organization_id,
        name=body.name,
        channel_type=body.channel_type,
        config_enc=encrypt_secret(json.dumps(body.config)),
        is_active=body.is_active,
    )
    db.add(row)
    write_audit(db, user_id=user.id, organization_id=user.organization_id, action="notification.channel.create", target=body.name)
    db.commit()
    db.refresh(row)
    return ChannelOut.model_validate(row)


@router.post("/channels/{channel_id}/test")
def test_channel(db: DbSession, user: CurrentUser, channel_id: uuid.UUID) -> dict:
    _require_admin(user)
    channel = db.scalar(
        select(NotificationChannel).where(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == user.organization_id,
        )
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    config = json.loads(decrypt_secret(channel.config_enc))
    ok, err = send_to_channel(channel, config, "BFIntel test notification — channel configuration OK.")
    write_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="notification.channel.test",
        target=str(channel_id),
        result="success" if ok else "failed",
        metadata={"error": err},
    )
    db.commit()
    if not ok:
        raise HTTPException(status_code=502, detail=err or "send failed")
    return {"status": "sent"}
