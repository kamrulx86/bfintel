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


def ingest_alerts_file(db: Session, organization_id: UUID) -> dict[str, int]:
    settings = get_correlation_settings()
    path = settings.alerts_json_path
    stats = {"lines": 0, "normalized": 0, "skipped": 0, "errors": 0}

    if not os.path.isfile(path):
        stats["error"] = "file_missing"
        return stats

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

    file_size = os.path.getsize(path)
    if state.byte_offset > file_size:
        state.byte_offset = 0

    with open(path, "rb") as fh:
        fh.seek(state.byte_offset)
        chunk = fh.read(4 * 1024 * 1024)
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
