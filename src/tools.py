""" Tools the asset review agent can call."""

from datetime import date
from src.db import get_connection


REVIEW_DATE = date(2026, 11, 18)
ENDING_SOON_DAYS = 730  # about 24 months: one budget cycle plus migration lead time

def compute_support_status(deployment_model, end_of_support_date, review_date = REVIEW_DATE):
    """Returns the support status of the asset on the review date"""
    if deployment_model in ('saas', 'in_house'):
        return "not_applicable"

    if end_of_support_date is None:
        return "unknown"

    end_date = date.fromisoformat(end_of_support_date)
    if end_date < review_date:
        return "end_of_support"
    if (end_date-review_date).days <= ENDING_SOON_DAYS:
        return "ending_soon"
    return "supported"

def days_until_end_of_support(end_of_support_date, review_date=REVIEW_DATE):
    """Days from the review date to end of support; negative if alreay passed."""
    if end_of_support_date is None:
        return None
    return (date.fromisoformat(end_of_support_date)-review_date).days

def get_asset(asset_id):
    """Return the full record for one asset, with its computed support status."""
    asset_id = asset_id.strip().upper()

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM assets WHERE asset_id = ?", (asset_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return {"error": "asset_not_found", "asset_id": asset_id}

    asset = dict(row)

    asset["support_status"] = compute_support_status(
        asset["deployment_model"], asset["end_of_support_date"]
    )
    asset["days_until_end_of_support"] = days_until_end_of_support(
        asset["end_of_support_date"]
    )
    return asset
