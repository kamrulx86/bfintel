from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("bfintel", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_default_queue = "default"
celery_app.conf.beat_schedule = {
    "poll-wazuh-alerts-every-minute": {
        "task": "bfintel.poll_wazuh_alerts",
        "schedule": 60.0,
    },
    "enrich-source-ips-every-five-minutes": {
        "task": "bfintel.enrich_source_ips",
        "schedule": 300.0,
    },
    "evaluate-rules-every-two-minutes": {
        "task": "bfintel.evaluate_automation_rules",
        "schedule": 120.0,
    },
}
from app.workers import tasks as _tasks  # noqa: F401, E402
