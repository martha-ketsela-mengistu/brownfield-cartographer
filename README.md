# The Brownfield Cartographer

The Brownfield Cartographer is a polyglot, agentic code analysis tool that builds a comprehensive knowledge graph of your legacy codebases. It combines static structural analysis (The Surveyor) with deep data lineage tracing (The Hydrologist) to help teams navigate, untangle, and modernize complex systems.

## Features

- **Multi-Language Support**: Analyzes Python, SQL, and YAML using `tree-sitter` for precise AST parsing.
- **Data Lineage Tracing**: Extracts table dependencies from SQL (`sqlglot` with dbt support), Python scripts (pandas/spark heuristics), and YAML (Airflow/dbt configs).
- **Module Graph**: Builds an import graph of your application and calculates PageRank to identify core architectural hubs.
- **Impact Analysis**: Track data lineage upstream (sources) or downstream (blast radius).
- **Interactive Visualization**: Generates rich, interactive HTML graph visualizations for both structural dependencies and data lineage.
- **Robust Pipeline**: Handles unparseable files gracefully to ensure partial results are always generated.

## Installation

This project uses `uv` for fast dependency management.

1. Clone this repository:
   ```bash
   git clone <repository_url>
   cd brownfield-cartographer
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

You can run the cartographer against a local repository path or a remote GitHub URL.

### 1. Analyze a Repository

The `analyze` command runs the full pipeline (Surveyor + Hydrologist) sequentially and serializes the graphs to the `.cartography/` folder.

```bash
# Analyze a local directory
uv run python -m src.cli analyze target_repo/jaffle-shop

# Alternatively, analyze a remote GitHub repository (it will be cloned automatically and cleaned up afterwards)
uv run python -m src.cli analyze https://github.com/dbt-labs/jaffle-shop
```

This will:
- Process all `.py`, `.sql`, and `.yaml`/`.yml` files.
- Compute the top PageRank hubs.
- Generate `.cartography/module_graph.json` and `.cartography/lineage_graph.json`.
- Render HTML visualisations in `.cartography/visualizations/`.

### 2. Query Data Lineage

Once a repository has been analyzed, you can query the data lineage graph.

**Trace Upstream Sources** for a dataset:
```bash
uv run python -m src.cli lineage customers
```

**Determine Blast Radius** (downstream impacts) for a dataset:
```bash
uv run python -m src.cli blast-radius ecom_raw_customers
```
