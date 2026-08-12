---
name: orchestrating-verified-changes
description: >
  Coordinates subagents for a change that crosses layers (data model,
  API, UI) or touches contracts/auth, on an existing project.
  Dispatches only the subagents relevant to the affected layers,
  hands off scope through a written Change Plan rather than full
  conversation context, and runs a capped Reflexion loop between
  verification and implementation. Use only after
  triaging-change-scope routes here — do not invoke directly for
  small changes.
---

# Orchestrating Verified Changes

For changes that genuinely span layers or carry risk. Lighter than a greenfield rebuild — this coordinates targeted subagents for maintenance work, not a full rewrite.

## Step 0: Write the Change Plan

Before dispatching anyone, write `docs/change/Change_Plan.md` containing only:

- The exact request, one line.
- Affected files (from triage).
- What "done" means — the specific, checkable outcome.

This file, not the conversation so far, is what subagents receive. Each subagent reads this file plus only the source files it needs — not the full orchestration history.

## Step 1: Dispatch only relevant subagents

Choose from these, don't run all of them by default:

- `auditing-affected-contracts` — only if the change touches an API or data contract. Documents the exact current contract before it changes.
- `implementing-change` — always runs. Makes the edit, scoped strictly to the Change Plan's file list.
- `verifying-change` — always runs. Executes the real build/test/lint step and reports raw output.

Skip subagents for layers the change doesn't touch. A UI-only change doesn't need a data-layer auditor.

## Step 2: Reflexion loop (capped)

1. `verifying-change` runs the actual check and appends raw output to `docs/change/Verification_Log.md` — append the specific failure only, not a full re-dump of prior state.
2. `implementing-change` reads only the latest failure entry, fixes the specific cause, re-triggers verification.
3. Cap at 3 iterations. On the 3rd failure, stop and hand the real error back to the user instead of continuing to guess. Repeated blind iteration under pressure to resolve is exactly where fabrication creeps in.

## Step 3: Close out

Every subagent still follows `grounding-before-editing`, `scoped-late-stage-changes`, and `verifying-before-claiming-done`. This orchestrator adds coordination on top of those — it doesn't replace them.

Delete `docs/change/` once the change ships. It's a scratch handoff artifact, not permanent documentation.

## Why this keeps context small

- Subagents read a short Change Plan and specific files, not the full conversation.
- The Reflexion loop passes single error entries forward, never accumulated logs.
- The triage gate upstream means this orchestrator only fires when coordination is actually worth its overhead.
