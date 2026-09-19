from app.services.rule_templates import RULE_TEMPLATES, get_template


def test_rule_templates_catalog():
    assert len(RULE_TEMPLATES) >= 5
    ids = {t["id"] for t in RULE_TEMPLATES}
    assert "ssh-brute-high-risk" in ids
    assert all(t.get("conditions_summary") for t in RULE_TEMPLATES)


def test_get_template():
    tpl = get_template("critical-session")
    assert tpl is not None
    assert tpl["conditions"]["all"]
    assert get_template("missing-id") is None
