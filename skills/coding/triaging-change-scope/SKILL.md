---
name: triaging-change-scope
description: >
  Runs first on every request to classify its size and decide whether
  to handle it directly (single agent, minimal context) or dispatch
  to the multi-agent orchestrator (orchestrating-verified-changes).
  Use this before any other skill fires — it is the entry point that
  prevents small changes from triggering full multi-agent context
  overhead.
---

# Triaging Change Scope

Classify the request before doing anything else.

## Tier 1 — Micro change (handle solo, no subagents)

Signals: single file, no schema/API contract change, cosmetic/config/copy/style edit, a bug fix isolated to one function.

Action: apply `grounding-before-editing`, `scoped-late-stage-changes`, and `verifying-before-claiming-done` directly. Do not dispatch subagents. Do not open audit/docs files unless directly relevant to the one file being touched.

## Tier 2 — Multi-file, same-layer change (handle solo, read wider)

Signals: touches 2-5 files within one layer (e.g. only API routes, or only UI components), no architecture change.

Action: same three guardrail skills, but explicitly list every affected file before editing. Still no subagent dispatch — coordinating agents costs more context than one agent reading five files.

## Tier 3 — Cross-cutting or high-risk change (dispatch to orchestrator)

Signals: touches data layer + API + UI together, changes an API contract, touches auth/permissions, or the request spans "the whole X flow."

Action: dispatch to `orchestrating-verified-changes`.

## Rule

Default to the lowest tier that plausibly covers the request. Escalate mid-task only if the change turns out bigger than scoped — don't pre-emptively over-scope "to be safe." Over-scoping is exactly what burns context on small changes.
