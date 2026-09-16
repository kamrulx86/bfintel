import re
from urllib.parse import quote

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.attack_session import AttackSession
from app.models.normalized_event import NormalizedEvent
from app.schemas.investigation import SearchHit, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

_IP_RE = re.compile(r"^[\d.a-fA-F:*]+$")


@router.get("", response_model=SearchResponse)
def global_search(
    db: DbSession,
    user: CurrentUser,
    q: str = Query(min_length=1, max_length=128),
    limit: int = Query(default=20, ge=1, le=50),
) -> SearchResponse:
    query = q.strip()
    org_id = user.organization_id
    results: list[SearchHit] = []
    seen: set[str] = set()

    def add(hit: SearchHit) -> None:
        key = f"{hit.type}:{hit.label}"
        if key in seen or len(results) >= limit:
            return
        seen.add(key)
        results.append(hit)

    if _IP_RE.match(query):
        ip_rows = db.scalars(
            select(AttackSession.source_ip)
            .where(AttackSession.organization_id == org_id, AttackSession.source_ip.ilike(f"%{query}%"))
            .distinct()
            .limit(limit)
        ).all()
        for ip in ip_rows:
            add(SearchHit(type="source_ip", label=ip, href=f"/app/sources/{quote(ip, safe='')}", meta="Source IP"))

    host_rows = db.scalars(
        select(NormalizedEvent.target_host)
        .where(
            NormalizedEvent.organization_id == org_id,
            NormalizedEvent.target_host.isnot(None),
            NormalizedEvent.target_host.ilike(f"%{query}%"),
        )
        .distinct()
        .limit(limit)
    ).all()
    for host in host_rows:
        add(
            SearchHit(
                type="hostname",
                label=host,
                href=f"/app/attacks?host={quote(host, safe='')}",
                meta="Target host",
            )
        )

    user_rows = db.scalars(
        select(NormalizedEvent.username)
        .where(
            NormalizedEvent.organization_id == org_id,
            NormalizedEvent.username.isnot(None),
            NormalizedEvent.username.ilike(f"%{query}%"),
        )
        .distinct()
        .limit(limit)
    ).all()
    for username in user_rows:
        add(
            SearchHit(
                type="username",
                label=username,
                href=f"/app/attacks?username={quote(username, safe='')}",
                meta="Username",
            )
        )

    try:
        from uuid import UUID

        session_id = UUID(query)
        session = db.scalar(
            select(AttackSession).where(AttackSession.organization_id == org_id, AttackSession.id == session_id)
        )
        if session:
            add(
                SearchHit(
                    type="attack_session",
                    label=str(session.id),
                    href=f"/app/sources/{quote(session.source_ip, safe='')}",
                    meta=f"Session · {session.source_ip}",
                )
            )
    except ValueError:
        pass

    return SearchResponse(query=query, results=results[:limit])
