# Brownfield Cartographer Constitution

<!--
SYNC IMPACT REPORT
- Version change: N/A → 0.1.0
- Modified principles: N/A (new constitution)
- Added sections: Cross-Cutting Requirements; Engineering Workflow & Quality Gates; Governance (project-specific)
- Removed sections: N/A
- Templates requiring updates:
  - ✅ updated: g:\projects\brownfield-cartographer\.specify\templates\plan-template.md
  - ✅ updated: g:\projects\brownfield-cartographer\.specify\templates\tasks-template.md
  - ✅ no change required: g:\projects\brownfield-cartographer\.specify\templates\spec-template.md
  - ✅ no change required: g:\projects\brownfield-cartographer\.specify\templates\checklist-template.md
- Deferred items:
  - TODO(RATIFICATION_DATE): Unknown adoption date; set when first ratified by repo owners.
-->

## Core Principles

### Clean Architecture (Non‑Negotiable)
- The system MUST enforce clear boundaries between domain (core logic), application orchestration,
  interface adapters (CLI/API), and infrastructure (I/O, parsers, graph storage).
- Domain logic MUST NOT import infrastructure concerns (filesystem, network, LLM clients, DB drivers).
- Cross-cutting concerns (logging, config, tracing, error types) MUST be injected or passed explicitly,
  not accessed via hidden globals.

**Rationale**: Keeps analysis logic testable and portable across target repos and environments.

### Strong Data Models (Non‑Negotiable)
- All knowledge graph nodes/edges and persisted artifacts MUST use explicit schemas (e.g., Pydantic).
- Public models MUST be versioned and backwards compatible (or include a migration plan).
- Parsers/analyzers MUST return typed results; “dict soup” is not an acceptable interface.

**Rationale**: A code intelligence system is only as reliable as its schema discipline.

### Proper Logging & Traceability (Non‑Negotiable)
- The system MUST emit structured logs suitable for programmatic inspection.
- Every analysis action MUST be attributable (agent/component, input file, evidence range if applicable)
  and MUST be recorded in an append-only trace artifact (e.g., `cartography_trace.jsonl`).
- Logs MUST avoid leaking secrets (tokens, credentials, raw customer data).

**Rationale**: You need auditability and trust when inferring architecture from imperfect signals.

### Comprehensive Testing (Non‑Negotiable)
- Tests MUST be included for all critical paths (parsing, graph construction, query operations).
- New/changed behavior MUST be covered by unit tests; end-to-end behavior MUST have integration tests.
- Tests MUST be deterministic and runnable in CI (no network-required tests without explicit gating).

**Rationale**: The tool is used under time pressure; correctness must be dependable.

### Error Handling & Graceful Degradation (Non‑Negotiable)
- The system MUST fail gracefully on unparseable or unexpected files: log, skip, and continue when safe.
- Errors MUST be represented with typed error models that preserve context (file, component, root cause).
- User-facing errors MUST be actionable (what failed, where, and how to proceed).

**Rationale**: Real brownfield repos are messy; robustness is a product requirement.

### Performance & Cost Discipline
- The system MUST be designed to scale to very large repos (hundreds of thousands of LOC).
- Expensive operations (LLM calls, full scans) MUST be minimized via caching, incremental updates,
  and batching where appropriate.
- The system MUST track performance and spend budgets (time, tokens) for analysis runs.

**Rationale**: A cartographer is only useful if it’s fast enough for day-one onboarding.

### Security & Safe-by-Default Operation
- The system MUST treat repositories as untrusted input (no executing repo code during analysis).
- File access MUST be least-privilege: read-only for target repos; writes only under `.cartography/`.
- Any network calls (e.g., LLM providers) MUST be explicit, configurable, and redact sensitive content.

**Rationale**: You will analyze production-like codebases and must avoid creating new risks.

### Code Quality Standards
- Public interfaces MUST be documented and stable (CLI contract, schemas, output artifact formats).
- Code MUST be linted/formatted and type-checked where applicable.
- Complexity MUST be justified; prefer simple, composable analyzers over monolithic “do everything” flows.

**Rationale**: This is an engineering system, not a one-off script.

## Cross-Cutting Requirements

- **Outputs as contracts**: Persisted artifacts (e.g., `module_graph.json`, `lineage_graph.json`,
  `CODEBASE.md`, `onboarding_brief.md`, `cartography_trace.jsonl`) are part of the public contract and
  MUST remain compatible across versions or include migrations.
- **Evidence discipline**: Any generated claims (especially LLM-derived) MUST be labeled with provenance
  (static analysis vs. inference) and include citations when possible (file + line range).
- **Configuration**: Runtime configuration MUST be explicit (CLI flags and/or config file), never hidden.

## Engineering Workflow & Quality Gates

- **Before merging**: automated checks MUST pass: lint/format, type checks (if used), and tests.
- **Review standard**: reviewers MUST verify architecture boundaries and that new features include
  logging, error handling, and tests per this constitution.
- **Performance guardrails**: changes that materially increase run time/cost MUST include benchmarks or
  a rationale and mitigation (cache/incremental mode).

## Governance

- **Supremacy**: This constitution supersedes other templates and conventions in this repository.
- **Amendments**: Any change MUST update this file, include a brief rationale in the PR/commit message,
  and update dependent templates under `.specify/templates/` to stay consistent.
- **Versioning policy**: Semantic versioning \(MAJOR.MINOR.PATCH\):
  - MAJOR: remove/relax a non-negotiable requirement or redefine governance materially
  - MINOR: add a new principle/section or materially expand requirements
  - PATCH: clarifications/wording with no change in obligations
- **Compliance checks**: Planning artifacts MUST include a “Constitution Check” section that lists the
  gates relevant to the feature and how they will be satisfied.

**Version**: 0.1.0 | **Ratified**: TODO(RATIFICATION_DATE) | **Last Amended**: 2026-03-11

