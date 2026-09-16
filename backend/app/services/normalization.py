import re
from datetime import datetime, timezone
from typing import Any, Optional

AUTH_FAIL_GROUPS = {
    "authentication_failed",
    "authentication_failures",
    "invalid_login",
    "win_authentication_failed",
}
AUTH_SUCCESS_GROUPS = {"authentication_success", "authentication_successful"}
SERVICE_HINTS = {
    "sshd": "ssh",
    "ssh": "ssh",
    "win_authentication": "rdp",
    "rdp": "rdp",
    "ftp": "ftp",
    "smtp": "smtp",
    "apache": "web",
    "nginx": "web",
}


def _parse_ts(value: str) -> datetime:
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value.replace("+0000", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _extract_ip(data: dict[str, Any], full_log: str) -> Optional[str]:
    for key in ("srcip", "src_ip", "source_ip", "win_srcip"):
        if data.get(key):
            return str(data[key]).split(":")[0]
    m = re.search(r"srcip[=:\s]+(\S+)", full_log, re.I)
    if m:
        return m.group(1).split(":")[0]
    m = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", full_log)
    if m and not full_log.strip().startswith("{"):
        return m.group(0)
    return None


def _infer_service(groups: list[str], decoder: str, location: str) -> str:
    blob = " ".join(groups + [decoder, location]).lower()
    for hint, svc in SERVICE_HINTS.items():
        if hint in blob:
            return svc
    if "sshd" in blob or "ssh" in blob:
        return "ssh"
    return "authentication"


def is_auth_related(groups: list[str], rule_id: str) -> bool:
    gset = {g.lower() for g in groups}
    if gset & AUTH_FAIL_GROUPS or gset & AUTH_SUCCESS_GROUPS:
        return True
    if rule_id in {"5710", "5712", "5716", "5720", "5760", "5551"}:
        return True
    return any("authentication" in g for g in gset)


def normalize_wazuh_alert(alert: dict[str, Any]) -> Optional[dict[str, Any]]:
    rule = alert.get("rule") or {}
    groups = rule.get("groups") or []
    if not isinstance(groups, list):
        groups = []
    rule_id = str(rule.get("id", ""))
    if not is_auth_related(groups, rule_id):
        return None

    data = alert.get("data") or {}
    full_log = alert.get("full_log") or ""
    agent = alert.get("agent") or {}
    decoder = (alert.get("decoder") or {}).get("name") or ""

    gset = {g.lower() for g in groups}
    if gset & AUTH_SUCCESS_GROUPS or rule_id in {"5501", "5503"}:
        auth_result = "success"
    elif gset & AUTH_FAIL_GROUPS or rule_id in {"5710", "5712", "5720", "5760"}:
        auth_result = "failure"
    else:
        auth_result = "unknown"

    source_ip = _extract_ip(data, full_log)
    username = data.get("srcuser") or data.get("dstuser") or data.get("user")
    if isinstance(username, str) and "(" in username:
        username = username.split("(")[0].strip()

    wazuh_id = str(alert.get("id") or alert.get("_id") or "")
    if not wazuh_id:
        return None

    return {
        "wazuh_event_id": wazuh_id,
        "timestamp": _parse_ts(str(alert.get("timestamp", ""))),
        "source_ip": source_ip,
        "destination_ip": data.get("dstip") or data.get("dst_ip"),
        "source_port": _maybe_int(data.get("srcport")),
        "destination_port": _maybe_int(data.get("dstport")),
        "protocol": data.get("protocol"),
        "username": username,
        "target_host": agent.get("name") or alert.get("location"),
        "agent_id": str(agent.get("id")) if agent.get("id") is not None else None,
        "agent_name": agent.get("name"),
        "rule_id": rule_id,
        "rule_level": rule.get("level"),
        "rule_description": rule.get("description"),
        "authentication_result": auth_result,
        "service": _infer_service(groups, decoder, str(alert.get("location", ""))),
        "event_type": "authentication",
        "raw_event": alert,
    }


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
