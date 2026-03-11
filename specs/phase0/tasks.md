# Tasks: The Brownfield Cartographer

**Input**: Design documents from `/specs/phase0/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED by the repository constitution. Include unit and integration tests for
all critical paths and any new/changed behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create Cartographer project structure (src/analyzers, src/agents, src/graph, src/cli, src/util, tests/)
- [ ] T002 Initialize Python project with pyproject.toml and core dependencies in the repo root
- [ ] T003 [P] Configure linting, formatting, and type-checking tools (e.g., ruff/black/mypy) for src/ and tests/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement configuration loader in src/util/config.py (CLI + agents shared settings)
- [ ] T005 [P] Implement structured logging and trace writer in src/util/logging.py and src/util/trace.py
- [ ] T006 [P] Implement error model and centralized error handling utilities in src/util/errors.py
- [ ] T007 Define core Pydantic models for ModuleNode, DatasetNode, TransformationNode, and edges in src/graph/models.py
- [ ] T008 Implement knowledge graph wrapper around NetworkX in src/graph/knowledge_graph.py
- [ ] T009 Setup test scaffolding (pytest config, conftest) in tests/unit/ and tests/integration/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - FDE generates a system map (Priority: P1) 🎯 MVP

**Goal**: Enable an FDE to run a single command against a brownfield repo and receive CODEBASE.md,
module and lineage graphs sufficient to answer the Five FDE Day-One questions.

**Independent Test**: Run the CLI against a target repo and verify that CODEBASE.md, onboarding_brief,
module_graph, and lineage_graph are generated and usable to answer the Day-One questions.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for analyze CLI entrypoint in tests/contract/test_cli_analyze.py
- [ ] T011 [P] [US1] Integration test for full system map generation in tests/integration/test_system_map_generation.py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement LanguageRouter and tree-sitter initialization in src/analyzers/language_router.py
- [ ] T013 [P] [US1] Implement Surveyor static analyzer for module graph (imports, functions, classes) in src/agents/surveyor.py
- [ ] T014 [P] [US1] Implement basic module graph construction using NetworkX in src/graph/module_graph.py
- [ ] T015 [US1] Implement analyze command in src/cli/cartographer_cli.py to run Surveyor and persist module_graph.json to .cartography/
- [ ] T016 [US1] Generate initial CODEBASE.md (Architecture Overview, Critical Path, High-Velocity files placeholder) in src/agents/archivist.py
- [ ] T017 [US1] Wire end-to-end analysis pipeline in src/orchestrator.py (Surveyor → Graph → Archivist) and ensure trace logging via util/trace.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - FDE investigates lineage and blast radius (Priority: P2)

**Goal**: Allow an FDE to inspect upstream and downstream lineage for datasets and compute blast radius
for modules across Python and SQL code.

**Independent Test**: For a known dbt or Airflow-style repo, lineage and blast_radius queries must
match manually derived upstream/downstream dependencies.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T018 [P] [US2] Contract test for trace_lineage interface in tests/contract/test_trace_lineage.py
- [ ] T019 [P] [US2] Integration test for lineage + blast_radius on a sample dbt/SQL project in tests/integration/test_lineage_and_blastradius.py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement Python data flow analyzer (pandas/PySpark read/write) in src/analyzers/python_dataflow_analyzer.py
- [ ] T021 [P] [US2] Implement SQL lineage analyzer using sqlglot for dbt models and raw SQL in src/analyzers/sql_lineage_analyzer.py
- [ ] T022 [US2] Merge Python and SQL lineage into DataLineageGraph in src/agents/hydrologist.py
- [ ] T023 [US2] Implement blast_radius and trace_lineage graph queries in src/graph/lineage_queries.py
- [ ] T024 [US2] Extend Archivist to persist lineage_graph.json and update CODEBASE.md Data Sources & Sinks section in src/agents/archivist.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - FDE asks semantic questions via Navigator (Priority: P3)

**Goal**: Provide an interactive Navigator agent that can explain modules and locate implementations of
business concepts using semantic analysis grounded in code and graphs.

**Independent Test**: For a known repo, Navigator’s explain_module and find_implementation answers must
match the source code and cite correct files and line ranges.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T025 [P] [US3] Contract test for Navigator tools API in tests/contract/test_navigator_tools.py
- [ ] T026 [P] [US3] Integration test for explain_module and find_implementation on a sample repo in tests/integration/test_navigator_semantics.py

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement ContextWindowBudget component for LLM calls in src/util/context_budget.py
- [ ] T028 [P] [US3] Implement Semanticist agent to generate purpose statements and detect Documentation Drift in src/agents/semanticist.py
- [ ] T029 [US3] Implement Navigator agent with tools (find_implementation, trace_lineage, blast_radius, explain_module) in src/agents/navigator.py
- [ ] T030 [US3] Integrate Navigator with existing graphs and CODEBASE.md, exposing a CLI or REPL in src/cli/navigator_cli.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Incremental Optimization & Cross-Cutting Concerns

**Purpose**: Make the Cartographer efficient and sustainable for ongoing FDE engagements.

- [ ] T031 Implement git-diff based incremental analysis mode in src/orchestrator_incremental.py
- [ ] T032 [P] Add performance benchmarks for full vs incremental runs in tests/integration/test_performance_incremental.py
- [ ] T033 [P] Add unit tests for ContextWindowBudget accuracy and enforcement in tests/unit/test_context_budget.py
- [ ] T034 [P] Documentation updates for CLI usage and CODEBASE.md semantics in docs/ and specs/phase0/quickstart.md
- [ ] T035 Security hardening review and updates (e.g., avoiding sensitive content in logs) across src/util/logging.py and agents

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion; can run in parallel with User Story 1 once foundations are ready
- **User Story 3 (Phase 5)**: Depends on User Stories 1 and 2 providing graphs and CODEBASE.md context
- **Incremental Optimization (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on having a working module graph; remains logically independent of Navigator
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on graphs and CODEBASE.md from US1/US2 but should be independently testable via Navigator scenarios

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core analyzers and models before agents
- Agents before CLI or external interfaces
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (system map + CODEBASE.md)
4. **STOP and VALIDATE**: Test User Story 1 independently against a real target repo
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase 6 optimizations and performance improvements

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Surveyor, module graph, Archivist basics)
   - Developer B: User Story 2 (Hydrologist, lineage graph, blast_radius)
   - Developer C: User Story 3 (Semanticist, Navigator, ContextWindowBudget)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

