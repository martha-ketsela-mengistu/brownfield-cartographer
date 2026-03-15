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
   git clone https://github.com/martha-ketsela-mengistu/brownfield-cartographer.git
   cd brownfield-cartographer
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

The Cartographer provides two main entry points: **Analyze** (to build the knowledge graph) and **Query** (to interact with it via the AI Navigator).

### 1. Analyze a Repository

Point the Cartographer at a local directory or a GitHub URL. This builds the structural and data lineage graphs.

```bash
# Analyze a GitHub repo
uv run python -m src.cli analyze https://github.com/dbt-labs/jaffle_shop

# Analyze a local path incrementally
uv run python -m src.cli analyze ./target_repo --incremental
```

**What it produces**:
- `.cartography/CODEBASE.md`: A synthesized context for AI coding agents.
- `.cartography/onboarding_brief.md`: Answers to the Five FDE Day-One Questions.
- `.cartography/module_graph.json`: Structural import graph.
- `.cartography/lineage_graph.json`: Data lineage graph.
- `.cartography/visualizations/`: Interactive HTML maps of your code.

### 2. Query the Navigator (Interactive AI)

Once analyzed, use the Navigator agent to investigate the codebase.

```bash
# General implementation query
uv run python -m src.cli query "Where is the revenue calculation?"

# Data lineage query
uv run python -m src.cli query --path target_repo/jaffle-shop "What upstream sources feed the 'orders' table?"

# Impact analysis (Blast Radius)
uv run python -m src.cli query --path target_repo/jaffle-shop "What breaks if I change src/models/staging/stg_orders.sql?"
```

## Features
- **Surveyor Agent**: Static AST analysis (tree-sitter), PageRank hubs, and cyclomatic complexity.
- **Hydrologist Agent**: Cross-language data lineage (Python + SQL + YAML).
- **Semanticist Agent**: LLM-powered purpose extraction and **Documentation Drift** detection.
- **Archivist Agent**: Living context generation (`CODEBASE.md`) and audit trail logging.
- **Navigator**: LangGraph-powered query agent with tools for graph traversal and semantic search.
