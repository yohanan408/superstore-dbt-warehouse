# Superstore dbt Warehouse

An analytics-engineering project on the US Superstore orders data. It loads the raw orders into PostgreSQL, models them into a star schema with dbt, tests the models, and uses Power BI to explore shipping lead times and loss patterns.

**Stack:** Python • PostgreSQL • SQLAlchemy • dbt Core • Power BI

> **Note on scope:** This is a small, single-machine project on a public 9,994-row dataset. It demonstrates modeling, transformation, and testing practices, not production-scale infrastructure.

## Architecture

```
orders CSV ──► ingestion/ingest_raw_data.py ──► raw.superstore_transactions (9,994 rows)
                                                         │
                                                         ▼
                                                   [dbt models]
                                                         │
                          ┌──────────────────────────────┴───────────────────┐
                          ▼                                                  ▼
                dim_products (1,894 products)  ◄── many-to-one (*:1) ──  fact_orders (9,994 rows)
                                                         │
                                                         ▼
                                                     Power BI
```

## Components

- **Ingestion** (`ingestion/ingest_raw_data.py`, SQLAlchemy): reads the Orders CSV, normalizes column names, converts currency and date columns (with an explicit date format), checks that nothing was lost in conversion, and reloads `raw.superstore_transactions`. Re-running it replaces the data instead of duplicating it. The connection string comes from the `DATABASE_URL` environment variable.
- **Transformation** (dbt Core): `models/dim_products.sql` and `models/fact_orders.sql` restructure the raw table into a star schema. `fact_orders` carries calculated lead times and a loss flag.
- **Data tests** (`models/schema.yml`): `not_null` and `unique` tests on the product keys in `dim_products` and on `fact_orders.row_id`, plus a `not_null` test on `fact_orders.quantity`.
- **BI layer:** the star schema feeds a Power BI report on shipping lead times and loss rates.
  <img width="756" height="422" alt="image" src="https://github.com/user-attachments/assets/9a218521-7012-4c4d-b5a0-8016f70f5052" />


## Findings

- **Reused product IDs:** 32 product IDs in the raw file are shared by more than one product name (1,862 unique IDs, 1,894 ID/name combinations), which would cause many-to-many join collisions. The product dimension uses a surrogate key built from an MD5 hash of composite columns instead.
- **Shipping delays:** An order line is flagged as an SLA violation when it ships more than 5 days after the order date. All 1,824 violations (18.3% of order lines) are Standard Class, the only mode with lead times above 5 days. Violation counts are highest for Office Supplies every month (174 in December, 162 in September), but this mostly reflects volume: Office Supplies is about 60% of order lines, and September, November and December carry roughly twice the order volume of other months. Within Standard Class, the violation rate is similar across categories (29–31%) and regions (29–32%). Counts are summed across 2014–2017.
- **Shipping mode vs. loss rate:** The share of loss-making order lines is 15.8% for Second Class, 18.0% for Same Day, 19.1% for First Class and 19.7% for Standard Class. Second Class is lowest, but when tested on whole orders (5,009 of them) the difference across the four modes is not statistically significant (chi-square p ≈ 0.09). Discount level, not shipping mode, drives losses: in every mode, 95–99% of lines discounted above 20% lose money, versus about 5–7% of the rest. The dataset has no shipping-cost column, so no cost-based explanation can be drawn from it.

These figures were first verified in a pandas analysis.

## Quickstart

1. Install PostgreSQL, create the `demand_aw_dw` database, and create the `raw.superstore_transactions` table.
2. Install the dependencies (`pandas`, `sqlalchemy`, `psycopg2-binary`, `dbt-postgres`).
3. Export the "Orders" sheet of the dataset as `US Superstore data - Orders.csv` and place it next to the ingestion script.
4. Load the raw table (Windows cmd; use `export` on macOS/Linux):

```bash
set DATABASE_URL=postgresql://postgres:<password>@localhost:5432/demand_aware_dw
python ingestion/ingest_raw_data.py
```

5. Create a dbt profile at `~/.dbt/profiles.yml`. The profile name must match `profile:` in `dbt_project.yml`; the values below are placeholders.

```yaml
demand_aware_pipeline:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      password: "{{ env_var('PGPASSWORD') }}"
      dbname: demand_aware_dw
      schema: staging
```

6. Build and test the models:

```bash
dbt debug    # checks the connection
dbt run      # builds dim_products and fact_orders
dbt test     # runs the schema.yml tests
```

## Repository Layout

```
superstore-dbt-warehouse/
├── ingestion/
│   └── ingest_raw_data.py
├── models/
│   ├── dim_products.sql
│   ├── fact_orders.sql
│   └── schema.yml
├── analyses/ macros/ seeds/ snapshots/ tests/   # empty (.gitkeep)
├── .gitignore                  # target/, logs/, dbt_packages/, .env
├── dbt_project.yml
└── README.md
```

`target/` and `logs/` are generated by dbt and are not tracked.

## Limitations

- One 9,994-row table loaded manually into a local PostgreSQL instance; there is no scheduling, incremental loading, or cloud warehouse.
- There is no staging layer between the raw table and the final models.
- The tests cover keys and nulls only; there is no referential-integrity or business-rule testing yet.
- The findings are descriptive and based on historical data.

## Roadmap

- [ ] Add a staging model (`stg_superstore_transactions`) and build the dimension and fact tables from it.
- [ ] Add a `relationships` test from `fact_orders` to `dim_products`, and a singular test that ship date is not before order date.
- [ ] Add the raw-table SQL and a `docker-compose.yml` with a Postgres service so the project runs with one command.
- [ ] Add a GitHub Actions workflow that starts Postgres, loads the CSV, and runs `dbt build`.
- [ ] Put the findings queries in `analyses/`, and publish `dbt docs` with a lineage-graph screenshot.

## Data

The project uses the US Superstore sales dataset (9,994 order lines). [https://www.kaggle.com/datasets/juhi1994/superstore]

## License

MIT. See [[LICENSE](LICENSE)]
