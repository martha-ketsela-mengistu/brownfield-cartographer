# Five FDE Day-One Answers

## 1. What is the primary data ingestion path?
Data enters the system through the **Source Layer**, defined in `models\staging\__sources.yml`. This file maps physical tables in the `raw` schema (e.g., `rawcustomers`, `raworders`, `rawitems`) to logical dbt sources. From there, data flows into the **Staging Layer** (e.g., `models\staging\stg_orders.sql`) where raw columns are renamed and standardized before reaching the Mart layer.

## 2. What are the 3-5 most critical output datasets/endpoints?
The most critical value providers are the **Mart Layer** tables, specifically:
1.  **`models\marts\customers.sql`**: Provides customer lifetime value (CLV) and behavior summaries.
2.  **`models\marts\orders.sql`**: Enriched order data with financial metrics and order type classification.
3.  **`models\marts\order_items.sql`**: Granular line-item data enabling revenue and cost analysis.
These models serve as the consolidated views for segmentation, retention, and revenue attribution.

## 3. What is the blast radius if the most critical module fails?
A failure in the **Staging Layer** (e.g., `models\staging\stg_orders.sql`) has the highest blast radius. Because the Lineage Graph contains 18 nodes and 17 edges with a linear flow, breaking a staging model breaks all dependent Marts. Specifically, if `stg_orders` fails, `models\marts\orders.sql` and `models\marts\order_items.sql` will fail, halting all order and revenue analytics.

## 4. Where is the business logic concentrated vs. distributed?
Business logic is **concentrated in SQL** within the `models\` directory (e.g., CLV calculations in `models\marts\customers.sql`) and **reusable utilities in Macros** (e.g., `macros\cents_to_dollars.sql`). Infrastructure logic is distributed across **Configuration** (`dbt_project.yml`, `packages.yml`) and **Orchestration** (`.github\workflows\ci.yml`, `Taskfile.yml`), which handle deployment and environment setup rather than data transformation.

## 5. What has changed most frequently in the last 90 days?
Based on the Hotspots velocity data, **Configuration and Tooling files** show the only recorded activity.
*   **`.pre-commit-config.yaml`**: 1 commit (Code quality standards).
*   **`packages.yml`**: 1 commit (Dependency management).
All core data models (`models\`), macros, and workflows show **0 commits**, indicating a stable codebase with recent changes limited to development environment hygiene and dependency pinning.