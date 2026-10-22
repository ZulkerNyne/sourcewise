# Sourcewise engineering instructions

Read PROJECT_PLAN.md and docs/roadmap.md before changes. Implement one coherent
milestone at a time. Explain inputs, outputs, concepts, and tradeoffs before major
components; explain test results and limitations afterward. Let the learner review
before moving into a substantially different component.

Selected approved sources determine all religious content. Never supplement them
with pretrained knowledge or unselected texts. Enforce source scope in backend
permissions and database/retrieval filters, not just prompts. Require evidence or
conservative abstention; failed retrieval does not prove absence from a book.
Preserve Arabic originals, versions, scholarly attribution, and translation provenance.
Never invent quotations or page numbers. Resolve citations from stored metadata.
Deterministically validate references and authorization, independently assess semantic
support, and require qualified human review for ambiguous interpretations. Automated
checks are fallible; never promise zero contamination or theological infallibility.
Do not issue personalized fatwas or publish unreviewed generated religious materials.

Use typed Python and explicit error handling. Run pytest, Ruff lint and format checks
for relevant changes. Keep CI and documentation current. Do not claim unrun checks
passed. Never commit secrets, student data, or unauthorized copyrighted material.
Use synthetic nonreligious fixtures until licensed materials receive human approval.
Do not implement later phases without an explicit new task. Use the existing isolated
checkout; do not create worktrees unless the user requests one.

## Commit identity

The user requires all commits to use the name `ZulkerNyne`. Before committing,
set repository-local user.name to ZulkerNyne and user.email to
ZulkerNyne@users.noreply.github.com. Verify author and committer identity; do not
inherit the cloud image's default identity.
