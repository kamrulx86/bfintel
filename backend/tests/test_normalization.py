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


def test_skips_non_auth_alert():
    alert = {
        "id": "1",
        "timestamp": "2026-09-16T12:00:00.000+0000",
        "rule": {"id": "100", "groups": ["syslog"], "description": "Generic"},
        "agent": {"id": "001", "name": "x"},
    }
    assert normalize_wazuh_alert(alert) is None
