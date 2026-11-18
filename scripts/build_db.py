"""Build the SQLite inventory database from the CSV files in data/."""

import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "inventory.db"

SCHEMA = """
CREATE TABLE assets (
    asset_id                TEXT PRIMARY KEY,
    product_name            TEXT NOT NULL,
    version                 TEXT,
    vendor                  TEXT NOT NULL,
    asset_type              TEXT NOT NULL
        CHECK (asset_type IN ('operating_system', 'database', 'runtime', 'application')),
    deployment_model        TEXT NOT NULL
        CHECK (deployment_model IN ('on_premises', 'cloud_managed', 'saas', 'in_house')),
    business_criticality    TEXT NOT NULL
        CHECK (business_criticality IN ('high', 'medium', 'low')),
    data_sensitivity        TEXT NOT NULL
        CHECK (data_sensitivity IN ('restricted', 'confidential', 'internal')),
    annual_maintenance_cost INTEGER,
    end_of_support_date     TEXT,
    lifecycle_source_url    TEXT,
    lifecycle_checked_date  TEXT
);

CREATE TABLE dependencies (
    asset_id            TEXT NOT NULL REFERENCES assets(asset_id),
    depends_on_asset_id TEXT NOT NULL REFERENCES assets(asset_id),
    PRIMARY KEY (asset_id, depends_on_asset_id),
    CHECK (asset_id <> depends_on_asset_id)
);
"""


def blank_to_none(value):
    """Turn an empty CSV field into None so SQLite stores NULL."""
    value = value.strip()
    return value if value else None


def to_int_or_none(value):
    """Convert a numeric CSV field to int, keeping blanks as None."""
    value = blank_to_none(value)
    return int(value) if value is not None else None


def read_csv(path):
    """Read a CSV file into a list of dicts keyed by column name."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_assets(conn, rows):
    for row in rows:
        conn.execute(
            "INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row["asset_id"].strip(),
                row["product_name"].strip(),
                blank_to_none(row["version"]),
                row["vendor"].strip(),
                row["asset_type"].strip(),
                row["deployment_model"].strip(),
                row["business_criticality"].strip(),
                row["data_sensitivity"].strip(),
                to_int_or_none(row["annual_maintenance_cost"]),
                blank_to_none(row["end_of_support_date"]),
                blank_to_none(row["lifecycle_source_url"]),
                blank_to_none(row["lifecycle_checked_date"]),
            ),
        )


def load_dependencies(conn, rows):
    for row in rows:
        conn.execute(
            "INSERT INTO dependencies VALUES (?, ?)",
            (row["asset_id"].strip(), row["depends_on_asset_id"].strip()),
        )


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    assets = read_csv(DATA_DIR / "assets.csv")
    dependencies = read_csv(DATA_DIR / "dependencies.csv")
    load_assets(conn, assets)
    load_dependencies(conn, dependencies)

    conn.commit()
    conn.close()
    print(f"Built {DB_PATH.name}: {len(assets)} assets, {len(dependencies)} dependencies")


if __name__ == "__main__":
    main()