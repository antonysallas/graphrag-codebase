from src.mcp.utils.query_guardrails import MAX_RESULTS_ABSOLUTE, MAX_RESULTS_DEFAULT, enforce_limit


def test_enforce_limit_adds_missing() -> None:
    query = "MATCH (n:Task) RETURN n"
    result = enforce_limit(query)
    assert f"LIMIT {MAX_RESULTS_DEFAULT}" in result


def test_enforce_limit_caps_excessive() -> None:
    query = "MATCH (n:Task) RETURN n LIMIT 5000"
    result = enforce_limit(query)
    assert f"LIMIT {MAX_RESULTS_ABSOLUTE}" in result


def test_enforce_limit_preserves_small() -> None:
    query = "MATCH (n:Task) RETURN n LIMIT 10"
    result = enforce_limit(query)
    assert "LIMIT 10" in result


def test_enforce_limit_handles_semicolon() -> None:
    query = "MATCH (n:Task) RETURN n;"
    result = enforce_limit(query)
    assert f"LIMIT {MAX_RESULTS_DEFAULT}" in result
    assert result.endswith(f"LIMIT {MAX_RESULTS_DEFAULT}")
    assert ";" not in result  # Should be stripped or handled (SPEC says rstrip(';'))


def test_enforce_limit_with_custom_limit() -> None:
    query = "MATCH (n:Task) RETURN n"
    result = enforce_limit(query, max_results=50)
    assert "LIMIT 50" in result


def test_enforce_limit_with_custom_limit_excessive() -> None:
    query = "MATCH (n:Task) RETURN n"
    result = enforce_limit(query, max_results=5000)
    assert f"LIMIT {MAX_RESULTS_ABSOLUTE}" in result
