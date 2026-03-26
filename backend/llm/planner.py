def classify_query(q):
    q = q.lower()
    if "trace" in q:
        return "TRACE_ORDER"
    if "top" in q:
        return "AGGREGATION"
    if "not" in q:
        return "ANOMALY"
    return "GENERAL"