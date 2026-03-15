# Five FDE Day-One Answers

## 1. What is the primary data ingestion path?
Data enters the system via raw e-commerce tables defined in **`models\staging\__sources.yml`** (e.g., `ecom.rawcustomers`, `ecom.raworders`) and is ingested either through synthetic generation orchestrated by **`Taskfile.yml`** or direct warehouse connection. The transformation path flows linearly: **Source Tables** → **Staging Models** (`models\staging\stg_*.sql`) → **Mart Models** (`models\marts\*.sql`).

## 2. What are the 3-5 most critical output datasets/endpoints?
The highest value outputs are the mart-layer models designed for business intelligence and segmentation:
1.  **`models\marts\customers.sql`**: Provides customer lifetime value (LTV) and segmentation (new vs. returning) per **`models\marts\customers.yml`**.
2.  **`models\marts\orders.sql`**: Aggregates financial metrics (total, tax, cost) and order composition for revenue analysis per **`models\marts\orders.yml`**.
3.  **`models\marts\order_items.sql`**: Enables granular revenue analysis by product category and cost tracking per **`models\marts\order_items.yml`**.

## 3. What is the blast radius if the most critical module fails?
If **`models\staging\stg_orders.sql`** fails, the blast radius is high: it directly breaks **`models\marts\orders.sql`** and cascades to **`models\marts\customers.sql`** (which enriches customer data with order metrics). Additionally, failure of the shared macro **`macros\cents_to_dollars.sql`** (marked `Drift: True`) would corrupt monetary calculations across multiple staging models (`stg_orders`, `stg_products`, `stg_supplies`), invalidating financial integrity downstream.

## 4. Where is the business logic concentrated vs. distributed?
Business logic is **concentrated in SQL** within the `models/` directory (transformations in **`models\staging\stg_orders.sql`**, aggregations in **`models\marts\orders.sql`**) and **`macros/`** (universal rules like **`macros\cents_to_dollars.sql`**). Configuration logic (timezone, variables) is centralized in **`dbt_project.yml`**. Python is strictly reserved for Ops/CI orchestration (**`.github\workflows\scripts\dbt_cloud_run_job.py`**, **`Taskfile.yml`**) and contains no transformation logic.

## 5. What has changed most frequently in the last 90 days?
Based on the `Drift: True` status indicating instability or high churn, the **Staging Layer** and **Core Macros** are the most volatile areas. Specifically, **`models\staging\stg_orders.sql`**, **`models\staging\stg_supplies.sql`**, and **`macros\cents_to_dollars.sql`** are marked `Drift: True`, suggesting frequent adjustments to ingestion transformations and currency conversion logic compared to the stable Mart layer (`Drift: False`).