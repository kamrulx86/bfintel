from app.services.normalization import normalize_wazuh_alert


def test_normalize_ssh_auth_failure():
    alert = {
        "id": "1234567890.12345",
        "timestamp": "2026-09-16T12:00:00.000+0000",
        "rule": {
            "id": "5710",
            "level": 5,
            "description": "sshd: authentication failed.",
            "groups": ["authentication_failed", "sshd"],
        },
        "agent": {"id": "001", "name": "lab-host"},
        "data": {"srcip": "203.0.113.10", "srcuser": "root", "srcport": "54321"},
        "decoder": {"name": "sshd"},
        "location": "/var/log/auth.log",
    }
    norm = normalize_wazuh_alert(alert)
    assert norm is not None
    assert norm["source_ip"] == "203.0.113.10"
    assert norm["authentication_result"] == "failure"
    assert norm["service"] == "ssh"
    assert norm["wazuh_event_id"] == "1234567890.12345"


def test_normalize_wazuh_user_activity_login_failed():
    alert = {
        "id": "1789776234.14575",
        "timestamp": "2026-09-19T06:03:53.917486+06:00",
        "rule": {
            "id": "110003",
            "level": 5,
            "description": "User Activity | Login failed",
            "groups": ["user_activity", "user_activity", "login_failed"],
        },
        "agent": {"id": "002", "name": "srv-node-01"},
        "data": {"srcip": "113.190.252.123", "srcport": "35602", "dstuser": "root"},
        "decoder": {"name": "sshd"},
        "full_log": "Failed password for root from 113.190.252.123 port 35602 ssh2",
    }
    norm = normalize_wazuh_alert(alert)
    assert norm is not None
    assert norm["authentication_result"] == "failure"
    assert norm["source_ip"] == "113.190.252.123"


def test_skips_non_auth_alert():
    alert = {
        "id": "1",
        "timestamp": "2026-09-16T12:00:00.000+0000",
        "rule": {"id": "100", "groups": ["syslog"], "description": "Generic"},
        "agent": {"id": "001", "name": "x"},
    }
    assert normalize_wazuh_alert(alert) is None
