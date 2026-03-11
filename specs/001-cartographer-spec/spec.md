# Feature Specification: The Brownfield Cartographer

**Feature Branch**: `001-cartographer-spec`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Create a comprehensive technical specification for 'The Brownfield Cartographer,' a multi-agent codebase intelligence system. The spec must include: Agentic Architecture: Define the orchestration of the Surveyor (Static Structure), Hydrologist (Data Lineage), Semanticist (LLM Analysis), and Archivist (Deliverables). Static & Semantic Analysis: Detail the integration of tree-sitter for Python/SQL/YAML parsing and sqlglot for cross-dialect SQL lineage. Include a strategy for Documentation Drift detection by comparing implementation code against existing docstrings. Graph Schema: Define Pydantic models for the Knowledge Graph, specifically ModuleNodes (path, complexity, velocity), DatasetNodes (storage type, schema), and the PRODUCES/CONSUMES/IMPORTS edge relationships. Data Lineage Logic: Specify the methodology for building a NetworkX DiGraph that bridges Python data operations (pandas/PySpark) with SQL CTE/JOIN chains to calculate blast radius and upstream dependencies. Output Generation: Define the schema for CODEBASE.md, including sections for the Critical Path, Data Sinks, and High-Velocity files, alongside the Onboarding Brief answering the five FDE Day-One questions. The Navigator Toolset: Specify the LangGraph implementation for an interactive query agent with tools for find_implementation, trace_lineage, blast_radius, and explain_module. Performance & Cost: Include a specification for a ContextWindowBudget to track LLM spend and an Incremental Update mode using git diffs to avoid full-repo re-analysis."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - FDE generates a system map (Priority: P1)

An FDE points the Cartographer at a previously unseen brownfield data-platform repository (e.g., dbt +
Airflow). They run a single command and receive a CODEBASE.md plus graphs that clearly show modules,
critical-path components, and data lineage across Python, SQL, and YAML, without needing to understand
the repo structure in advance.

**Why this priority**: This is the primary onboarding use case; without it, the Cartographer does not
deliver core value.

**Independent Test**: Run the CLI against a target repo; verify that CODEBASE.md and graph artifacts
are generated and that the FDE can answer the Five Day-One questions using only those outputs.

**Acceptance Scenarios**:

1. **Given** a supported target repo path, **When** the user runs the analyze command, **Then** the
   system produces CODEBASE.md, onboarding_brief, module_graph, and lineage_graph artifacts.
2. **Given** a generated CODEBASE.md, **When** the user inspects the Critical Path and Data Sinks
   sections, **Then** the listed modules/datasets match the actual high-impact components of the repo.

---

### User Story 2 - FDE investigates lineage and blast radius (Priority: P2)

An FDE needs to understand what produces a particular analytical table and what will break if they
change a core transformation. Using the Cartographer, they query the lineage graph to view upstream
dependencies and run blast_radius to see downstream consumers across Python, SQL, and YAML.

**Why this priority**: Accurate lineage and blast-radius analysis are essential for safe changes in
data platforms.

**Independent Test**: Run lineage and blast-radius queries for known tables/modules in a target repo
with an existing DAG and verify that the reported sources/sinks match manually derived ground truth.

**Acceptance Scenarios**:

1. **Given** a target dataset identifier, **When** the user invokes trace_lineage for downstream or
   upstream traversal, **Then** the system returns a path of transformations with file and line
   references.
2. **Given** a module path in the repository, **When** the user runs blast_radius, **Then** the
   system returns all directly and indirectly affected datasets/modules.

---

### User Story 3 - FDE asks semantic questions via Navigator (Priority: P3)

An FDE wants to understand what a module does and where a business concept (e.g., revenue
calculation) is implemented. They use the Navigator agent to ask natural-language questions and
receive answers grounded in static analysis, lineage, and semantic summaries with explicit evidence.

**Why this priority**: Semantic search and explanation compress time-to-understanding for complex
codebases.

**Independent Test**: For a known codebase, run Navigator queries (explain_module, find_implementation)
and verify that answers are consistent with the source code and cite correct files and line ranges.

**Acceptance Scenarios**:

1. **Given** a module path, **When** the user calls explain_module via Navigator, **Then** the system
   returns a concise purpose description plus evidence (file and line range) consistent with the code.
2. **Given** a business concept string, **When** the user calls find_implementation, **Then** the
   system returns candidate modules/functions whose code actually implements that concept, not just
   those that mention it in comments or docstrings.

---

### Edge Cases

- What happens when the target repository contains files that tree-sitter or sqlglot cannot parse?
  The system must log structured errors, skip only the failing units, and complete analysis wherever
  possible.
- How does the system handle repositories without meaningful git history (e.g., shallow clones) when
  computing change velocity? It must fall back gracefully to static complexity metrics only.
- What happens when the repo has no SQL or YAML files (pure Python) or no Python (pure SQL/dbt)?
  The system must still construct a valid, possibly partial, graph and clearly mark missing modality
  coverage in outputs.
- How does the system behave when the repo is extremely large (e.g., hundreds of thousands of LOC)?
  It must support incremental analysis using git diffs and avoid full re-analysis on every run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST analyze a given repository path and produce a structured system map,
  including a module graph, data lineage graph, semantic index, CODEBASE.md, onboarding brief, and
  trace artifacts.
- **FR-002**: The system MUST implement a multi-agent architecture with distinct responsibilities for
  Surveyor (static structure), Hydrologist (data lineage), Semanticist (LLM analysis), Archivist
  (artifact generation), and a Navigator query interface.
- **FR-003**: The system MUST integrate tree-sitter to parse at least Python, SQL, and YAML files and
  extract module structure, imports, functions/classes, and relevant data operations.
- **FR-004**: The system MUST integrate sqlglot to parse SQL and dbt models across multiple dialects
  and extract table and CTE dependencies for inclusion in the lineage graph.
- **FR-005**: The system MUST implement Documentation Drift detection by comparing docstrings/comments
  with code-derived semantic summaries and flagging mismatches in outputs.
- **FR-006**: The system MUST define Pydantic models (or equivalent strong schemas) for core knowledge
  graph node types (ModuleNode, DatasetNode, TransformationNode) and edge relationships
  (IMPORTS, PRODUCES, CONSUMES, CALLS, CONFIGURES).
- **FR-007**: The system MUST build and persist a NetworkX (or equivalent) directed graph
  representation of modules, datasets, and transformations that supports lineage and blast-radius
  queries.
- **FR-008**: The system MUST compute and store complexity and velocity signals per module, including
  at least lines of code, basic complexity metrics, and change frequency derived from git history
  where available.
- **FR-009**: The system MUST generate CODEBASE.md with clearly defined sections for Architecture
  Overview, Critical Path, Data Sources & Sinks, High-Velocity Files, Known Debt (including drift and
  circular dependencies), and a module purpose index.
- **FR-010**: The system MUST generate an onboarding brief document that answers the Five FDE Day-One
  questions using evidence from the graphs and semantic analysis.
- **FR-011**: The system MUST expose a Navigator agent with tools for find_implementation,
  trace_lineage, blast_radius, and explain_module that operate over the shared knowledge graph.
- **FR-012**: The system MUST implement a ContextWindowBudget component that tracks LLM token spend,
  enforces per-run budgets, and selects model tiers accordingly (e.g., cheap model for bulk, premium
  for synthesis).
- **FR-013**: The system MUST support an Incremental Update mode that uses git diff (or equivalent
  change detection) to re-analyze only modified files and incrementally update the knowledge graph and
  artifacts.
- **FR-014**: The system MUST log all analysis actions and key decisions to an append-only trace file
  including timestamps, components, inputs, and outputs where feasible.
- **FR-015**: The system MUST avoid executing target repo code and treat the repository as untrusted
  input at all times.

### Key Entities *(include if feature involves data)*

- **ModuleNode**: Represents a source module or file; attributes include path, language, purpose
  statement, complexity score, change velocity, domain cluster, dead-code candidacy, and timestamps.
- **DatasetNode**: Represents a logical dataset/table/stream; attributes include name, storage type,
  schema snapshot, freshness expectations, owner, and source-of-truth flag.
- **TransformationNode**: Represents a transformation operation; attributes include source datasets,
  target datasets, transformation type, source file, line range, and raw SQL or code snippet
  references when applicable.
- **Edge Relationships**:
  - **IMPORTS**: module → module with weight or count of imports.
  - **PRODUCES**: transformation → dataset, capturing output lineage.
  - **CONSUMES**: transformation → dataset, capturing upstream dependencies.
  - **CALLS**: function → function, capturing call graph relationships.
  - **CONFIGURES**: config file → module/pipeline, capturing YAML or configuration links.
- **ContextWindowBudget**: Tracks per-run and per-operation token usage and limits, along with model
  tier selections and budget thresholds.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For supported codebases, the system generates CODEBASE.md and graph artifacts in under
  10 minutes for repositories up to 800k LOC on standard FDE hardware.
- **SC-002**: For target dbt or Airflow-based repos, the generated lineage graph matches at least
  90% of known upstream/downstream relationships verified against the native tooling (e.g., dbt
  lineage visualization).
- **SC-003**: At least 4 out of 5 FDE Day-One questions can be accurately answered using only the
  generated artifacts and Navigator tools for the chosen target repos.
- **SC-004**: Documentation Drift detection correctly flags at least 80% of intentionally injected
  docstring/implementation mismatches in controlled test repos.
- **SC-005**: Incremental Update mode reduces re-analysis time by at least 50% on subsequent runs
  where less than 10% of files have changed.
- **SC-006**: LLM token spend per full analysis run stays within a predefined budget threshold while
  maintaining acceptable accuracy for semantic tasks, as defined in project-level configuration.

## Assumptions

- Target environments have access to git history for most real-world repos, but the system must remain
  useful with limited or missing history.
- Users will primarily run the Cartographer via a CLI interface; deeper integrations (e.g., API,
  UI dashboards) are future enhancements and out of scope for this specification.
- Supported languages and frameworks at initial launch focus on Python + SQL + YAML for data
  engineering-style codebases; extensibility hooks will permit adding more languages later.

