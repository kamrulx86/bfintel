from uuid import UUID

from app.core.database import SessionLocal
from app.models.wazuh_connection import WazuhConnection
from app.services.enrichment import enrich_pending_ips
from app.services.rules_engine import evaluate_rules
from app.services.ingest_alerts import ingest_alerts_file, ingest_initial_wazuh_logs
from app.workers.celery_app import celery_app
from sqlalchemy import select


@celery_app.task(name="bfintel.initial_wazuh_ingest")
def initial_wazuh_ingest(organization_id: str) -> dict:
    """Background backfill after setup (completes large alert files + enrichment)."""
    db = SessionLocal()
    try:
        org_id = UUID(organization_id)
        stats = ingest_initial_wazuh_logs(db, org_id)
        db.commit()
        return {"status": "ok", **{k: v for k, v in stats.items() if k != "enrichment"}, "enrichment": stats.get("enrichment")}
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {"status": "error", "detail": str(exc)}
    finally:
        db.close()


@celery_app.task(name="bfintel.poll_wazuh_alerts")
def poll_wazuh_alerts() -> dict:
    db = SessionLocal()
    try:
        conn = db.scalar(select(WazuhConnection).where(WazuhConnection.is_active.is_(True)).limit(1))
        if not conn:
            return {"status": "no_connection"}
        stats = ingest_alerts_file(db, conn.organization_id)
        db.commit()
        enrich_stats = enrich_pending_ips(db, conn.organization_id, limit=15)
        db.commit()
        return {"status": "ok", **stats, "enrichment": enrich_stats}
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {"status": "error", "detail": str(exc)}
    finally:
        db.close()


@celery_app.task(name="bfintel.evaluate_automation_rules")
def evaluate_automation_rules() -> dict:
    db = SessionLocal()
    try:
        conn = db.scalar(select(WazuhConnection).where(WazuhConnection.is_active.is_(True)).limit(1))
        if not conn:
            return {"status": "no_connection"}
        stats = evaluate_rules(db, conn.organization_id)
        db.commit()
        return {"status": "ok", **stats}
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {"status": "error", "detail": str(exc)}
    finally:
        db.close()


@celery_app.task(name="bfintel.enrich_source_ips")
def enrich_source_ips(organization_id: str | None = None) -> dict:
    db = SessionLocal()
    try:
        org_id: UUID
        if organization_id:
            org_id = UUID(organization_id)
        else:
            conn = db.scalar(select(WazuhConnection).where(WazuhConnection.is_active.is_(True)).limit(1))
            if not conn:
                return {"status": "no_connection"}
            org_id = conn.organization_id
        stats = enrich_pending_ips(db, org_id, limit=30)
        db.commit()
        return {"status": "ok", **stats}
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return {"status": "error", "detail": str(exc)}
    finally:
        db.close()
