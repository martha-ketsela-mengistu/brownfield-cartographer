# Five FDE Day-One Answers

## 1. What is the primary data ingestion path? (How does data enter the system?)
Data enters via raw tables defined in the `ecom` schema (e.g., `rawcustomers`, `raworders`) as configured in **`models\staging\__sources.yml`**. These sources are ingested by staging models (**`models\staging\stg_*.sql`**) which perform initial cleaning. For local development and testing, synthetic data is generated and seeded into the database (default: BigQuery) using the **`Taskfile.yml`** automation pipeline (`jafgen`).

## 2. What are the 3-5 most critical output datasets/endpoints? (What provides value?)
The highest business value resides in the Loyalty domain marts, which aggregate cleaned staging data for analytics:
1.  **`models\marts\customers.sql`**: Customer lifetime value and behavior summary (Domain: Loyalty).
2.  **`models\marts\orders.sql`**: Enriched order dataset with cost aggregation and categorization (Domain: Loyalty).
3.  **`models\marts\order_items.sql`**: Granular transaction view linking orders to products (Domain: Loyalty).
These models are backed by semantic definitions in their corresponding **`*.yml`** files for BI consumption.

## 3. What is the blast radius if the most critical module fails? (What breaks downstream?)
Failure in **`macros\cents_to_dollars.sql`** has the widest blast radius. This macro is called by multiple staging models (**`models\staging\stg_orders.sql`**, **`models\staging\stg_products.sql`**, **`models\staging\stg_supplies.sql`**). A break here corrupts monetary calculations across all three streams, cascading failure to all downstream Loyalty marts (**`customers`**, **`orders`**, **`order_items`**) due to the 18-node lineage dependency chain.

## 4. Where is the business logic concentrated vs. distributed? (Is it in SQL, Python, or config?)
Business transformation logic is **concentrated in SQL** within the `models/` directory (e.g., **`models\staging\stg_orders.sql`** handles currency conversion and date truncation). Configuration and testing logic are **distributed in YAML** (**`dbt_project.yml`**, **`models\**\*.yml`**). Orchestration and CI/CD logic are **isolated in Python** and GitHub Actions (**`.github\workflows\scripts\dbt_cloud_run_job.py`**, **`.github\workflows\ci.yml`**).

## 5. What has changed most frequently in the last 90 days? (Based on git velocity patterns)
The **Staging Layer** shows the highest change velocity. Analysis flags indicate **`Drift: True`** for 11 files, predominantly in **`models\staging\`** (e.g., **`stg_customers.sql`**, **`stg_orders.sql`**, **`stg_supplies.yml`**). This suggests active refinement of data ingestion, cleaning logic, and schema definitions compared to the more stable Mart and Configuration layers.