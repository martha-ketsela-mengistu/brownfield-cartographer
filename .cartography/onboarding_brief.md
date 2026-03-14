# Five FDE Day-One Answers

## 1. What is the primary data ingestion path?
Data enters the system through raw tables defined in the `ecom` schema, which are then transformed by dbt.
*   **Production Definition:** Logical sources are configured in `models\staging\__sources.yml`, pointing to tables like `rawcustomers`, `raworders`, and `rawitems` within the `raw` schema.
*   **Local/Dev Mechanism:** The `Taskfile.yml` orchestrates local ingestion by generating synthetic seed data for `jaffle-data` and loading it into the database via the `dbt seed` command, ensuring reproducibility for development.

## 2. What are the 3-5 most critical output datasets/endpoints?
The highest value assets are the aggregated mart tables used for analytics and revenue segmentation.
*   **`models\marts\customers.sql`:** Calculates customer lifetime value (LTV), total spend, and retention status (new vs. returning).
*   **`models\marts\orders.sql`:** Enriches order records with financial dimensions (total cost, tax) and categorical flags (food/drink).
*   **`models\marts\order_items.sql`:** Provides granular transaction-level data linking orders to products and supply costs.
*   **`models\marts\metricflow_time_spine.sql`:** Foundational date table required for time-based aggregations and metric continuity.

## 3. What is the blast radius if the most critical module fails?
A failure in **`models\staging\stg_orders.sql`** would cascade to three downstream marts, halting core revenue analytics.
*   **Direct Impact:** Breaks `models\marts\orders.sql` and `models\marts\order_items.sql` as they directly depend on staged order data.
*   **Indirect Impact:** Breaks `models\marts\customers.sql`, which aggregates order history to calculate lifetime spend and purchase frequency.
*   **Evidence:** The lineage graph (18 nodes, 17 edges) indicates a tight coupling between staging and marts, and `stg_orders.sql` is marked with `Drift: True`, indicating it is a active change point.

## 4. Where is the business logic concentrated vs. distributed?
Business logic is **distributed** across SQL models for transformation, but **concentrated** in macros for utilities and Python for orchestration.
*   **Distributed (SQL):** Transformation logic (e.g., currency conversion, flagging food/drink items) is embedded within models like `models\staging\stg_orders.sql` and `models\staging\stg_products.sql`.
*   **Concentrated (Macros):** Reusable utilities like currency conversion are centralized in `macros\cents_to_dollars.sql` to ensure consistency across dialects (PostgreSQL, BigQuery, etc.).
*   **Concentrated (Python):** CI/CD orchestration logic is isolated in `.github\workflows\scripts\dbt_cloud_run_job.py`, handling job triggering and status polling.

## 5. What has changed most frequently in the last 90 days?
Based on `Drift: True` markers in the module samples, the **Staging Layer** and **CI/CD Orchestration** show the highest velocity.
*   **Staging Models:** `models\staging\stg_orders.sql`, `models\staging\stg_customers.sql`, and `models\staging\stg_supplies.yml` are marked with drift, suggesting frequent schema or logic adjustments in the ingestion layer.
*   **Orchestration Script:** `.github\workflows\scripts\dbt_cloud_run_job.py` is marked with `Drift: True`, indicating active iteration on the deployment pipeline logic.
*   **Stable Areas:** Core macros (`macros\cents_to_dollars.sql`) and project config (`dbt_project.yml`) show `Drift: False`, indicating stability in foundational utilities.