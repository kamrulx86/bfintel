from app.services.rule_conditions import match_conditions


def test_match_risk_score():
    ctx = {"risk_score": 75, "risk_level": "high", "attempt_count": 10}
    cond = {"all": [{"field": "risk_score", "op": "gte", "value": 60}]}
    assert match_conditions(ctx, cond)


def test_no_match():
    ctx = {"risk_score": 10, "attempt_count": 1}
    cond = {"all": [{"field": "attempt_count", "op": "gte", "value": 50}]}
    assert not match_conditions(ctx, cond)
