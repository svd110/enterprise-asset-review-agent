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

# ***********************************************************************************************

VALID_STATUSES = ("supported", "ending_soon", "end_of_support", "not_applicable", "unknown")


def list_assets(support_status=None):
    """Return a short summary of every asset, optionally filtered by support status."""
    if support_status is not None and support_status not in VALID_STATUSES:
        return {
            "error": "invalid_support_status",
            "support_status": support_status,
            "valid_values": list(VALID_STATUSES),
        }

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT asset_id, product_name, version, deployment_model, "
            "business_criticality, data_sensitivity, end_of_support_date "
            "FROM assets ORDER BY asset_id"
        ).fetchall()
    finally:
        conn.close()

    summaries = []
    for row in rows:
        status = compute_support_status(row["deployment_model"], row["end_of_support_date"])
        if support_status is not None and status != support_status:
            continue
        summaries.append({
            "asset_id": row["asset_id"],
            "product_name": row["product_name"],
            "version": row["version"],
            "business_criticality": row["business_criticality"],
            "data_sensitivity": row["data_sensitivity"],
            "support_status": status,
        })

    return {"assets": summaries, "count": len(summaries)}