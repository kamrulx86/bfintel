from app.middleware.rate_limit import _allow, reset_rate_limit_store


def test_rate_limit_bucket():
    reset_rate_limit_store()
    for _ in range(5):
        assert _allow("pytest:login:1.2.3.4", 5, 60)
    assert not _allow("pytest:login:1.2.3.4", 5, 60)
