from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.services.ip_investigation import get_ip_profile, get_ip_timeline
from app.schemas.investigation import IpInvestigationProfile, TimelineResponse

router = APIRouter(prefix="/ip-intelligence", tags=["ip-intelligence"])


@router.get("/{source_ip}", response_model=IpInvestigationProfile)
def ip_profile(db: DbSession, user: CurrentUser, source_ip: str) -> IpInvestigationProfile:
    profile = get_ip_profile(db, user.organization_id, source_ip.strip())
    if not profile:
        raise HTTPException(status_code=404, detail="No data for this source IP")
    return profile


@router.get("/{source_ip}/timeline", response_model=TimelineResponse)
def ip_timeline(
    db: DbSession,
    user: CurrentUser,
    source_ip: str,
    hours: int = Query(default=168, ge=1, le=720),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TimelineResponse:
    return get_ip_timeline(db, user.organization_id, source_ip.strip(), hours=hours, limit=limit, offset=offset)
