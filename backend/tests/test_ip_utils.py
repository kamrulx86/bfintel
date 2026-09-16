from app.services.ip_utils import classify_ip_scope


def test_private_ip():
    assert classify_ip_scope("192.168.1.1") == "private"


def test_public_ip():
    assert classify_ip_scope("8.8.8.8") == "public"
