# Implementation Plan: The Brownfield Cartographer

**Branch**: `phase0` | **Date**: 2026-03-11 | **Spec**: `specs/phase0/spec.md`  
**Input**: Feature specification from `specs/phase0/spec.md` and Week 4 Brownfield Cartographer brief.

**Note**: This plan prioritizes the 72-hour onboarding use case: get an FDE from zero to accurate
architectural understanding on a real brownfield data platform.

## Summary

The Brownfield Cartographer is a multi-agent codebase intelligence system that ingests a real
data-engineering codebase and produces a living knowledge graph, CODEBASE.md, and an interactive
Navigator for structural, lineage, and semantic queries. This plan delivers the system in six phases:
structural foundations, lineage graph construction, semantic layer, synthesis/Archivist, Navigator
interface, and incremental optimization. Early phases bias toward fast, reliable static analysis that
can produce a usable system map within the first 72 hours of an engagement.

## Technical Context

**Language/Version**: Python 3.11 (Cartographer implementation); target repos primarily Python, SQL, YAML  
**Primary Dependencies**: tree-sitter (multi-language parsing), sqlglot (SQL lineage), NetworkX
(graph), Pydantic (data models), LangGraph (Navigator agent orchestration), git CLI  
**Storage**: Local filesystem for `.cartography/` artifacts (JSON, markdown, JSONL trace); no database
required initially  
**Testing**: pytest with unit + integration test suites; tests run in CI and avoid external network
dependencies  
**Target Platform**: Linux/macOS development environments and CI agents; compatible with local
checkouts of large repos  
**Project Type**: CLI-first analysis tool with internal library components and agent flows  
**Performance Goals**: Full analysis for ~800k LOC repo in ≤10 minutes on standard FDE laptop; steady
memory usage compatible with CI runners; Navigator queries return in seconds  
**Constraints**: Must not execute target repo code; must respect token and time budgets for LLM calls;
must operate offline for static phases when no LLM is configured  
**Scale/Scope**: Designed for multi-hundred-thousand-LOC brownfield data platforms (dbt + Airflow or
similar), with extensibility for additional languages and frameworks later.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Clean Architecture**: Planned layering separates analyzers and models (domain) from CLI,
  storage, and LLM adapters (infrastructure). Cross-cutting concerns (logging, config, budget) will be
  injected into agents rather than accessed via globals.
- [x] **Strong Data Models**: Knowledge graph entities (ModuleNode, DatasetNode, TransformationNode) and
  edges will be modeled with Pydantic schemas and versioned artifact formats in `.cartography/`.
- [x] **Logging & Traceability**: A structured logging layer and `cartography_trace.jsonl` will record
  all analysis actions, including file paths, line ranges, and agent/component names.
- [x] **Comprehensive Testing**: Each phase includes explicit unit and integration tests for parsers,
  graph construction, and Navigator queries; tests will be deterministic and CI-friendly.
- [x] **Error Handling**: An error model and centralized handling will ensure unparseable files or
  lineage failures are logged and skipped without aborting the full run when safe.
- [x] **Performance & Cost**: Initial phases focus on efficient static analysis; later phases introduce
  ContextWindowBudget and incremental analysis using git diff to avoid full re-runs.
- [x] **Security**: The system treats target repos as untrusted input, never executes repo code, and
  writes only under `.cartography/`. Any LLM calls will redact sensitive data where possible.
- [x] **Code Quality**: The project will use formatting, linting, and type-checking where feasible, and
  keep analyzers small and composable rather than monolithic.

## Project Structure

### Documentation (this feature)

```text
specs/phase0/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── analyzers/           # tree-sitter + sqlglot based static and lineage analyzers
├── agents/              # Surveyor, Hydrologist, Semanticist, Archivist, Navigator
├── graph/               # Knowledge graph models and NetworkX integration
├── cli/                 # Cartographer CLI entrypoints
└── util/                # Logging, config, error handling, ContextWindowBudget

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single-project Python CLI + library with clear analyzer/agent/graph separation,
aligned with the Clean Architecture constitution principle.

## Complexity Tracking

At this stage, no constitution violations are anticipated. Any future deviation (e.g., additional
subprojects or frameworks) must be justified here with simpler alternatives evaluated and rejected.

