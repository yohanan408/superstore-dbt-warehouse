"""Load the US Superstore "Orders" CSV into the local PostgreSQL warehouse.

Target table: raw.superstore_transactions (must already exist; see the README).

Usage (Windows cmd):
    set DATABASE_URL=postgresql://postgres:<password>@localhost:5432/demand_aware_dw
    python ingest_raw_data.py [path\\to\\orders.csv]

The connection string is read from the DATABASE_URL environment variable so that
no credentials are stored in the repository.
"""
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_CSV = Path(__file__).resolve().parent / "US Superstore data - Orders.csv"
DATE_FORMAT = "%m/%d/%Y"          # change if your CSV uses another date format
TARGET_SCHEMA = "raw"
TARGET_TABLE = "superstore_transactions"
EXPECTED_ROWS = 9994
NUMERIC_COLS = ["sales", "quantity", "discount", "profit"]
DATE_COLS = ["order_date", "ship_date"]


def load_and_clean(csv_path):
    """Read the CSV, normalize column names, and convert numbers and dates."""
    df = pd.read_csv(csv_path, encoding="cp1252")

    # 'Row ID' -> 'row_id', 'Sub-Category' -> 'sub_category', etc.
    df.columns = [c.strip().lower().replace("-", "_").replace(" ", "_") for c in df.columns]

    # Strip currency symbols and thousands separators, then convert to numbers
    for col in NUMERIC_COLS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = (df[col].astype(str)
                       .str.replace("$", "", regex=False)
                       .str.replace(",", "", regex=False))
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse dates with an explicit format so day/month order is never guessed
    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col], format=DATE_FORMAT, errors="coerce")

    # Conversions use errors="coerce", so check that nothing silently became null
    missing = df[NUMERIC_COLS + DATE_COLS].isna().sum()
    if missing.any():
        raise ValueError(
            "Some values could not be converted (check DATE_FORMAT and the CSV):\n"
            + missing[missing > 0].to_string()
        )
    if len(df) != EXPECTED_ROWS:
        print(f"Warning: expected {EXPECTED_ROWS} rows but found {len(df)}.")
    return df


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("Set the DATABASE_URL environment variable, e.g. "
                 "postgresql://postgres:<password>@localhost:5432/demand_aware_dw")

    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    print(f"Reading {csv_path} ...")
    df = load_and_clean(csv_path)

    table = f"{TARGET_SCHEMA}.{TARGET_TABLE}"
    engine = create_engine(url)
    # One transaction: empty the table, reload it, and count the rows.
    # Re-running the script therefore replaces the data instead of duplicating it.
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table}"))
        df.to_sql(TARGET_TABLE, conn, schema=TARGET_SCHEMA, if_exists="append", index=False)
        loaded = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()

    print(f"Loaded {loaded} rows into {table}.")


if __name__ == "__main__":
    main()