"""Tests for the asset review tools."""

from datetime import date
from src.tools import compute_support_status, get_asset, list_assets

REVIEW = date(2026, 11, 18)


# ******************************************* Testing compute_support_status ****************************************************
def test_saas_is_not_applicable():
    assert compute_support_status("saas", None, REVIEW) == "not_applicable"


def test_in_house_is_not_applicable():
    assert compute_support_status("in_house", None, REVIEW) == "not_applicable"


def test_past_date_is_end_of_support():
    assert compute_support_status("on_premises", "2023-10-10", REVIEW) == "end_of_support"


def test_date_within_window_is_ending_soon():
    assert compute_support_status("on_premises", "2027-01-12", REVIEW) == "ending_soon"


def test_far_future_date_is_supported():
    assert compute_support_status("on_premises", "2031-10-14", REVIEW) == "supported"


def test_end_date_on_review_day_is_still_supported_by_vendor():
    assert compute_support_status("on_premises", "2026-11-18", REVIEW) == "ending_soon"


def test_day_before_review_is_end_of_support():
    assert compute_support_status("on_premises", "2026-11-17", REVIEW) == "end_of_support"


def test_missing_date_on_premises_is_unknown():
    assert compute_support_status("on_premises", None, REVIEW) == "unknown"

# ******************************************** Testing get_asset ***************************************************

def test_get_asset_returns_record_with_status():
    asset = get_asset("A05")
    assert asset["product_name"] == "Microsoft SQL Server"
    assert asset["support_status"] == "end_of_support"


def test_get_asset_keeps_missing_cost_as_none():
    assert get_asset("A02")["annual_maintenance_cost"] is None


def test_get_asset_saas_has_no_lifecycle():
    asset = get_asset("A11")
    assert asset["support_status"] == "not_applicable"
    assert asset["days_until_end_of_support"] is None


def test_get_asset_unknown_id_returns_error():
    assert get_asset("A99") == {"error": "asset_not_found", "asset_id": "A99"}


def test_get_asset_accepts_lowercase_id():
    assert get_asset("a05")["asset_id"] == "A05"

# ******************************************** Testing list_asset ***************************************************

def test_list_assets_returns_all_fifteen():
    assert list_assets()["count"] == 15


def test_list_assets_filters_end_of_support():
    ids = [a["asset_id"] for a in list_assets("end_of_support")["assets"]]
    assert ids == ["A01", "A04", "A05", "A09", "A10"]


def test_list_assets_filters_ending_soon():
    ids = [a["asset_id"] for a in list_assets("ending_soon")["assets"]]
    assert ids == ["A02", "A08", "A13"]


def test_list_assets_rejects_invalid_status():
    assert list_assets("expired")["error"] == "invalid_support_status"
