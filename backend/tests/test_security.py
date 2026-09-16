from app.core.security import hash_password, verify_password


def test_password_hash_roundtrip():
    h = hash_password("Correct-Horse-Battery-Staple-99!")
    assert verify_password("Correct-Horse-Battery-Staple-99!", h)
    assert not verify_password("wrong", h)
