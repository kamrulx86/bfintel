import json
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.correlation_config import get_correlation_settings
from app.models.ingestion_state import IngestionState
from app.models.normalized_event import NormalizedEvent
from app.services.correlation import correlate_event
from app.services.normalization import normalize_wazuh_alert

CHUNK_BYTES = 4 * 1024 * 1024


def _get_or_create_state(db: Session, organization_id: UUID, path: str) -> IngestionState:
    state = db.scalar(
        select(IngestionState).where(
            IngestionState.organization_id == organization_id,
            IngestionState.source == "alerts_json",
        )
    )
    if not state:
        state = IngestionState(organization_id=organization_id, file_path=path, byte_offset=0)
        db.add(state)
        db.flush()
    return state


def reset_ingestion_offset(db: Session, organization_id: UUID) -> None:
    settings = get_correlation_settings()
    state = _get_or_create_state(db, organization_id, settings.alerts_json_path)
    state.byte_offset = 0
    state.file_path = settings.alerts_json_path


def ingest_alerts_backfill(db: Session, organization_id: UUID, *, max_passes: int = 64) -> dict[str, int]:
    """Read alerts.json from the beginning until caught up (or max_passes)."""
    settings = get_correlation_settings()
    path = settings.alerts_json_path
    totals: dict[str, int] = {"lines": 0, "normalized": 0, "skipped": 0, "errors": 0, "passes": 0}

    if not os.path.isfile(path):
        totals["error"] = "file_missing"
        return totals

    reset_ingestion_offset(db, organization_id)
    file_size = os.path.getsize(path)

    for _ in range(max_passes):
        stats = ingest_alerts_file(db, organization_id)
        totals["passes"] += 1
        for key in ("lines", "normalized", "skipped", "errors"):
            totals[key] += stats.get(key, 0)
        if stats.get("error"):
            totals["error"] = stats["error"]
            break

        state = _get_or_create_state(db, organization_id, path)
        if state.byte_offset >= file_size:
            break
        if stats.get("lines", 0) == 0:
            break

    return totals


def ingest_initial_wazuh_logs(db: Session, organization_id: UUID) -> dict[str, int | dict[str, int]]:
    """First-time import from Wazuh alerts.json (used after setup and on empty DB)."""
    stats = ingest_alerts_backfill(db, organization_id)
    from app.services.enrichment import enrich_pending_ips

    stats["enrichment"] = enrich_pending_ips(db, organization_id, limit=50)
    return stats


def ingest_alerts_file(db: Session, organization_id: UUID) -> dict[str, int]:
    settings = get_correlation_settings()
    path = settings.alerts_json_path
    stats = {"lines": 0, "normalized": 0, "skipped": 0, "errors": 0}

    if not os.path.isfile(path):
        stats["error"] = "file_missing"
        return stats

    state = _get_or_create_state(db, organization_id, path)

    file_size = os.path.getsize(path)
    if state.byte_offset > file_size:
        state.byte_offset = 0

    with open(path, "rb") as fh:
        fh.seek(state.byte_offset)
        chunk = fh.read(CHUNK_BYTES)
        new_offset = fh.tell()

    if not chunk:
        state.byte_offset = new_offset
        state.file_path = path
        return stats

    text = chunk.decode("utf-8", errors="ignore")
    if not text.endswith("\n") and new_offset < file_size:
        last_nl = text.rfind("\n")
        if last_nl >= 0:
            partial = text[last_nl + 1 :]
            text = text[: last_nl + 1]
            new_offset -= len(partial.encode("utf-8"))
        else:
            return stats

    lines = text.splitlines()

    for line in lines:
        stats["lines"] += 1
        line = line.strip()
        if not line:
            continue
        try:
            alert = json.loads(line)
        except json.JSONDecodeError:
            stats["errors"] += 1
            continue

        norm = normalize_wazuh_alert(alert)
        if not norm:
            stats["skipped"] += 1
            continue

        exists = db.scalar(
            select(NormalizedEvent.id).where(NormalizedEvent.wazuh_event_id == norm["wazuh_event_id"])
        )
        if exists:
            stats["skipped"] += 1
            continue

        event = NormalizedEvent(organization_id=organization_id, **{k: v for k, v in norm.items() if k != "raw_event"}, raw_event=norm["raw_event"])
        db.add(event)
        db.flush()
        correlate_event(db, event, organization_id)
        stats["normalized"] += 1

    state.byte_offset = new_offset
    state.file_path = path
    return stats
