# Evaluation contract and limits

Phase 0 validates schemas only. No retrieval or answer-quality measurements exist.
The ten critical acceptance scenarios in PROJECT_PLAN.md remain future integration
acceptance tests; schema tests do not fulfill those end-to-end requirements.

Each future case follows evaluations/datasets/case.schema.json: stable case ID,
development/holdout split, question, selected edition IDs, exact document versions,
expected supporting passage references, expected evidence/abstention outcome,
category, and human review status. Empty references are valid for abstention cases.
Only approved reviewed cases enter the benchmark. Never log private student data.
Separate development and untouched holdout sets; record dataset, corpus, retriever,
embedding model, prompt, generator, and verifier versions per run. Treat imported
prompt injection as data, and include model timeout/malformed response scenarios.

## Planned metrics

- Recall@K: retrieved relevant passages / all reference relevant passages.
- Precision@K: relevant passages among top K / K; missing slots count as irrelevant.
- MRR: mean reciprocal rank of the first relevant passage (zero when none).
- Source violations: count and rate of retrieved or cited unauthorized passages.
- Claim support: supported claims / assessed substantive claims.
- Citation validity: existing, version-matched authorized citations / all citations.
- Citation support and attribution accuracy: human-reviewed supported/correctly
  attributed references / assessed references.
- Abstention: separately measure abstention on unanswerable and answerable cases.
- Cross-source contamination and unsupported claims: explicit counts and rates.
- Latency, errors, retries, token usage, and estimated cost by pipeline version.

Report denominators, skipped/failed cases, dataset size, uncertainty, and examples.
Zero applicable cases means undefined, not 100%. Arabic meaning and interpretive
accuracy require qualified human judgment; an LLM judge is supplementary. Preserve
raw sanitized run outputs and compare versions on the same benchmark. No single
metric proves religious correctness or absence of outside-knowledge contamination.

## Keyword inspection checks

Synthetic tests now cover SQL-scoped cross-edition isolation, unauthorized selection
rejection, Arabic normalization without output changes, ranking/limits, and exact
stored references. These are developer inspection checks on unreviewed text, not
completion of the end-to-end source-fidelity acceptance tests or a measured retrieval
quality benchmark. No Recall@K, Precision@K or MRR result exists yet.

## Approval-boundary tests

Synthetic reviews test exact-byte binding, per-page approval, untouched intake,
required attestations, approved/unreviewed separation, stale/corrupt input rejection,
withdrawal and local CLI execution. They establish software behavior in the local
operator trust model, not reviewer authority, actual rights, or religious accuracy.
