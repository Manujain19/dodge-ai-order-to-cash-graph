def is_valid_query(q):
    allowed = ["order","product","billing","payment"]
    return any(a in q.lower() for a in allowed)