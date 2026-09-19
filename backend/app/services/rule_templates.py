"""Built-in automation rule templates (import via API)."""

from typing import Any

RULE_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "ssh-brute-high-risk",
        "name": "SSH brute force — high risk",
        "description": "Notify when an active session shows elevated risk and repeated SSH failures.",
        "category": "brute_force",
        "severity": "high",
        "cooldown_minutes": 15,
        "conditions": {
            "all": [
                {"field": "risk_score", "op": "gte", "value": 60},
                {"field": "attempt_count", "op": "gte", "value": 10},
                {"field": "service", "op": "eq", "value": "ssh"},
            ],
        },
        "conditions_summary": "risk_score ≥ 60 · attempts ≥ 10 · service = ssh",
    },
    {
        "id": "critical-session",
        "name": "Critical risk session",
        "description": "Immediate alert for sessions scored critical by BFIntel correlation.",
        "category": "risk",
        "severity": "critical",
        "cooldown_minutes": 10,
        "conditions": {
            "all": [
                {"field": "risk_level", "op": "eq", "value": "critical"},
                {"field": "attempt_count", "op": "gte", "value": 5},
            ],
        },
        "conditions_summary": "risk_level = critical · attempts ≥ 5",
    },
    {
        "id": "successful-login-after-failures",
        "name": "Successful login after failures",
        "description": "Possible compromise — at least one success after multiple failed attempts.",
        "category": "compromise",
        "severity": "critical",
        "cooldown_minutes": 30,
        "conditions": {
            "all": [
                {"field": "successful_attempt_count", "op": "gte", "value": 1},
                {"field": "attempt_count", "op": "gte", "value": 3},
            ],
        },
        "conditions_summary": "successes ≥ 1 · failures ≥ 3",
    },
    {
        "id": "multi-target-spray",
        "name": "Multi-target password spray",
        "description": "Same source hitting many hosts — horizontal scanning pattern.",
        "category": "brute_force",
        "severity": "high",
        "cooldown_minutes": 20,
        "conditions": {
            "all": [
                {"field": "attempt_count", "op": "gte", "value": 15},
                {"field": "risk_score", "op": "gte", "value": 45},
            ],
        },
        "conditions_summary": "attempts ≥ 15 · risk_score ≥ 45",
    },
    {
        "id": "medium-noise-gate",
        "name": "Medium risk — batched alert",
        "description": "Lower-noise template for medium sessions; longer cooldown.",
        "category": "risk",
        "severity": "medium",
        "cooldown_minutes": 45,
        "conditions": {
            "all": [
                {"field": "risk_level", "op": "eq", "value": "medium"},
                {"field": "attempt_count", "op": "gte", "value": 8},
            ],
        },
        "conditions_summary": "risk_level = medium · attempts ≥ 8",
    },
    {
        "id": "high-risk-any-service",
        "name": "High risk — any service",
        "description": "Catch RDP, FTP, or web auth abuse when risk score is high.",
        "category": "risk",
        "severity": "high",
        "cooldown_minutes": 15,
        "conditions": {
            "all": [
                {"field": "risk_score", "op": "gte", "value": 70},
                {"field": "attempt_count", "op": "gte", "value": 5},
            ],
        },
        "conditions_summary": "risk_score ≥ 70 · attempts ≥ 5",
    },
    {
        "id": "watchlist-boost",
        "name": "High attempts — early warning",
        "description": "Early warning before risk score peaks; useful with watchlisted IPs.",
        "category": "monitoring",
        "severity": "medium",
        "cooldown_minutes": 30,
        "conditions": {
            "all": [
                {"field": "attempt_count", "op": "gte", "value": 5},
                {"field": "risk_score", "op": "gte", "value": 30},
            ],
        },
        "conditions_summary": "attempts ≥ 5 · risk_score ≥ 30",
    },
]


def get_template(template_id: str) -> dict[str, Any] | None:
    for tpl in RULE_TEMPLATES:
        if tpl["id"] == template_id:
            return tpl
    return None
