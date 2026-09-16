_OPS = {
    "eq": lambda a, b: a == b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "in": lambda a, b: a in b if isinstance(b, list) else a == b,
}


def match_conditions(ctx: dict, conditions: dict) -> bool:
    clauses = conditions.get("all") or []
    for clause in clauses:
        field = clause.get("field")
        op = clause.get("op", "eq")
        expected = clause.get("value")
        actual = ctx.get(field)
        fn = _OPS.get(op)
        if fn is None or actual is None:
            return False
        try:
            if not fn(actual, expected):
                return False
        except TypeError:
            return False
    return True
