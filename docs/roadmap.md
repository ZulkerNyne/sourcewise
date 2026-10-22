# Roadmap and actual state

PROJECT_PLAN.md preserves the complete specification, phase deliverables, learning
objectives, and completion gates.

| Phase | Deliverable and completion gate | State |
| --- | --- | --- |
| 0 | Installable Python foundation, source/citation models, tests, CI configuration, architecture and policy docs | Implemented and locally validated; hosted CI pending push |
| 1 | Approved source intake, stable versioned passages, keyword baseline, then evaluated semantic/hybrid search; inspect precise references | Not started |
| 2 | Evidence-first extractive answers, then bounded generation, citation and semantic verification, safe abstention and failure handling | Not started |
| 3 | Reviewed development/holdout benchmarks and reproducible retrieval/answer/reliability reports | Not started |
| 4 | Source-grounded lessons, tutoring, reviewed assessments, adaptive revision | Not started |
| 5 | Student/instructor/admin web workflows, permissions and learning progress | Not started |
| 6 | Deployment, security, observability, backups, performance and regression gates | Not started |
| 7 | Optional evaluated research, such as cross-lingual retrieval and rerankers | Not started |

## Phase 0 evidence

Python 3.12.14; uv 0.12.23. Editable install succeeded; 24 schema tests passed.
Ruff lint and formatting checks pass. A fresh isolated install was also tested.
GitHub Actions workflow is written, but no hosted run has been observed: there is
no pushed commit yet. Do not describe hosted CI as passing. No credentials or
services are needed for this phase. No religious texts or translations are included.

## Next review and milestone

Inspect Phase 0 before starting a substantially different component. Then choose one
legally usable text/edition, accompanying material if any, and a qualified reviewer.
Phase 1's first task is an intake manifest and reviewed synthetic-to-approved source
storage/segmentation path with stable versioned references and database constraints.
Implement filtered keyword retrieval before embeddings; keep all source-fidelity
acceptance scenarios as required future integration tests.
