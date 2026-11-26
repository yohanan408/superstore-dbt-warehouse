-- Creates the raw table that ingest_raw_data.py loads.
--
-- 1) Create the database once, from the default "postgres" database:
--      CREATE DATABASE demand_aware_dw;
-- 2) Then run this file while connected to demand_aware_dw:
--      psql -U postgres -d demand_aware_dw -f ingestion/create_raw_table.sql
--
-- It is safe to run more than once (IF NOT EXISTS) and never drops data.
-- Column names match the CSV headers after the script's normalization
-- ("Row ID" -> row_id, "Sub-Category" -> sub_category, ...).

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.superstore_transactions (
    row_id         INTEGER        PRIMARY KEY,
    order_id       TEXT           NOT NULL,
    order_date     DATE           NOT NULL,
    ship_date      DATE           NOT NULL,
    ship_mode      TEXT           NOT NULL,
    customer_id    TEXT           NOT NULL,
    customer_name  TEXT           NOT NULL,
    segment        TEXT           NOT NULL,
    country        TEXT           NOT NULL,
    city           TEXT           NOT NULL,
    state          TEXT           NOT NULL,
    postal_code    INTEGER        NOT NULL,  -- leading zeros are already lost in the source file (e.g. 1040 = 01040)
    region         TEXT           NOT NULL,
    product_id     TEXT           NOT NULL,
    category       TEXT           NOT NULL,
    sub_category   TEXT           NOT NULL,
    product_name   TEXT           NOT NULL,
    sales          NUMERIC(12, 4) NOT NULL,
    quantity       INTEGER        NOT NULL,
    discount       NUMERIC(4, 2)  NOT NULL,
    profit         NUMERIC(12, 4) NOT NULL
);

-- Checks after loading (expected: 9994 rows, row_id 1 to 9994):
--   SELECT COUNT(*), MIN(row_id), MAX(row_id) FROM raw.superstore_transactions;
--
-- To compare with a table you created by hand in pgAdmin, run in psql:
--   \d raw.superstore_transactions