import re
from typing import Optional

from loguru import logger

MAX_RESULTS_DEFAULT = 100
MAX_RESULTS_ABSOLUTE = 1000


def enforce_limit(query: str, max_results: int = MAX_RESULTS_DEFAULT) -> str:
    """
    Ensure query has a LIMIT clause, add one if missing.

    Args:
        query: Cypher query string
        max_results: Desired limit (capped at MAX_RESULTS_ABSOLUTE)

    Returns:
        Query with LIMIT clause enforced
    """
    # Cap at absolute maximum
    effective_limit = min(max_results, MAX_RESULTS_ABSOLUTE)

    # Check if LIMIT already exists
    limit_pattern = r"\bLIMIT\s+(\d+)"
    match = re.search(limit_pattern, query, re.IGNORECASE)

    if match:
        existing_limit = int(match.group(1))
        if existing_limit > MAX_RESULTS_ABSOLUTE:
            logger.warning(f"Capping LIMIT from {existing_limit} to {MAX_RESULTS_ABSOLUTE}")
            query = re.sub(
                limit_pattern, f"LIMIT {MAX_RESULTS_ABSOLUTE}", query, flags=re.IGNORECASE
            )
        return query

    # Add LIMIT clause before any trailing semicolon
    logger.debug(f"Adding LIMIT {effective_limit} to query")
    query = query.rstrip().rstrip(";")
    return f"{query} LIMIT {effective_limit}"


def validate_limit_param(limit: Optional[int]) -> int:
    """
    Validate user-provided limit parameter.

    Args:
        limit: User-provided limit or None

    Returns:
        Validated limit within allowed range
    """
    if limit is None:
        return MAX_RESULTS_DEFAULT

    if limit < 1:
        return 1

    if limit > MAX_RESULTS_ABSOLUTE:
        logger.warning(f"Requested limit {limit} exceeds max, using {MAX_RESULTS_ABSOLUTE}")
        return MAX_RESULTS_ABSOLUTE

    return limit
