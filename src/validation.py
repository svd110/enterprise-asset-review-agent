"""Checks the agent's answer against the database instead of trusting it."""

import re

from src.tools import REVIEW_DATE, get_asset

ASSET_ID = re.compile(r"\bA\d{2}\b")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def validate_answer(answer, retrieved_ids):
    """Return a list of (check name, passed, detail) for one answer."""
    checks = []
    cited = set(ASSET_ID.findall(answer))

    unretrieved = sorted(cited - retrieved_ids)
    checks.append((
        "cited assets were retrieved",
        not unretrieved,
        f"never retrieved: {', '.join(unretrieved)}" if unretrieved
        else f"{len(cited)} cited, all retrieved",
    ))

    real_dates = {REVIEW_DATE.isoformat()}
    for asset_id in cited:
        asset = get_asset(asset_id)
        if "error" not in asset and asset["end_of_support_date"]:
            real_dates.add(asset["end_of_support_date"])
    answer_dates = set(DATE.findall(answer))
    wrong_dates = sorted(answer_dates - real_dates)
    checks.append((
        "dates match the database",
        not wrong_dates,
        f"not in database: {', '.join(wrong_dates)}" if wrong_dates
        else f"{len(answer_dates)} dates checked",
    ))

    return checks