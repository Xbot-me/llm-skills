---
name: verifying-before-claiming-done
description: >
  Requires deterministic evidence before the agent tells the user a
  task, fix, or feature is complete or working. Use before any
  message that declares something done, fixed, or working — forces
  an actual build/lint/test run or a traced code path, and honest
  reporting when verification isn't possible, instead of asserting
  success.
---

# Verify Before Claiming Done

**Rule: never say "this works," "this is fixed," or "done" without deterministic evidence gathered in this turn.**

## Checklist before declaring completion

- [ ] Ran the project's build/compile step (or equivalent) and it succeeded. State the actual result, not a paraphrase — if you ran it, report what it actually returned.
- [ ] Ran the relevant tests. If none exist for this code path, manually traced the exact lines affected and can point to them.
- [ ] If verification isn't possible in this environment (no test harness, can't run the app), say so explicitly: "I couldn't verify this by running it — here's what changed and why it should address X, but please test before relying on it."
- [ ] Never fabricate console output, test results, stack traces, or logs to make something look verified. If output wasn't actually produced by a real run, don't present it as if it were.

## Reflexion loop on failure

If a check fails: read the actual error, fix the specific cause it points to, re-run. Don't guess at a fix and reassert success without re-checking.

## Why this matters here

This is the single biggest source of "made up bullshit" — an agent under pressure to sound finished will describe success it didn't actually observe. Making verification a required step (not a courtesy) closes that gap.
