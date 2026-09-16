from app.services.allowlist import is_ip_allowlisted


class _Entry:
    def __init__(self, value: str, entry_type: str = "ip"):
        self.value = value
        self.entry_type = entry_type


class _FakeScalars:
    def __init__(self, entries):
        self._entries = entries

    def all(self):
        return self._entries


class _FakeDb:
    def __init__(self, entries):
        self._entries = entries

    def scalars(self, _stmt):
        return _FakeScalars(self._entries)


def test_exact_ip_match():
    db = _FakeDb([_Entry("10.0.0.5")])
    assert is_ip_allowlisted(db, "org", "10.0.0.5")


def test_cidr_match():
    db = _FakeDb([_Entry("10.0.0.0/24", "cidr")])
    assert is_ip_allowlisted(db, "org", "10.0.0.99")


def test_no_match():
    db = _FakeDb([_Entry("192.168.1.1")])
    assert not is_ip_allowlisted(db, "org", "8.8.8.8")


def test_invalid_ip():
    db = _FakeDb([_Entry("10.0.0.0/8", "cidr")])
    assert not is_ip_allowlisted(db, "org", "not-an-ip")
