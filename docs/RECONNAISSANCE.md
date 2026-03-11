# Jaffle Shop Project Analysis

This document outlines the findings from analyzing the `dbt-labs/jaffle-shop` project.

### (1) What is the primary data ingestion path?

The project uses **dbt seeds** as the initial method to load data.

Specifically, the data is ingested by running the command:
`dbt seed --full-refresh --vars '{"load_source_data": true}'`
This command loads the static CSV files located in the `seeds/jaffle-data/` directory into data warehouse.

### (2) What are the 3-5 most critical output datasets/endpoints?

The most critical output datasets are:
1.  **`customers`** 
2.  **`orders`**
3.  **`order_items`**

### (3) What is the blast radius if the most critical module fails?

If the staging model `stg_orders` were to fail, all downstream models that reference it, such as `orders`, `customers`, and `order_items`, would also fail to build. This could render the entire core of the project's data unusable, as the final reporting tables (`customers`, `orders`) would be incomplete or missing.

### (4) Where is the business logic concentrated vs. distributed?

The business logic is **concentrated** in the `/models` folder. It contains: 
*   **Staging models** contains`stg_customers.sql`, `stg_orders.sql` ...
*   **Marts models** contains `customers.sql`, `orders.sql`...

### (5) What has changed most frequently in the last 90 days (git velocity map)?

Based on the commit history, the most frequently changed files in the last 90 days are related to **package management and project dependencies**.

Specifically:
*   `packages.yml`: Updated to manage external dbt packages.
*   `package-lock.yml`: Automatically updated when `packages.yml` changes.

### Reflection: What was hardest to figure out manually? Where did you get lost?

The hardest part was identifying the 3-5 most critical output datasets/endpoints.
