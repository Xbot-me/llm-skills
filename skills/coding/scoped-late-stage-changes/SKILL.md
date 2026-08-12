---
name: scoped-late-stage-changes
description: >
  Manages small, targeted change requests on an existing, largely
  finished project (e.g. "just change X", "fix this one thing",
  "tweak the button color"). Locks the agent into minimal-diff mode:
  touch only what's necessary, no drive-by refactors, no new
  dependencies or architecture changes unless explicitly asked. Use
  whenever the request is a modification to working code rather than
  new feature work.
---

# Scoped Editing for Late-Stage Changes

**Trigger:** any request to modify existing, working code rather than build something new.

## Before writing any code

1. State explicitly which files this touches: "This change touches: [file list]." Nothing outside that list gets modified.
2. If satisfying the request seems to require touching a file outside that list, STOP and say so before proceeding — don't silently expand scope.
3. Do not introduce new libraries, patterns, or abstractions that aren't already used in the project, unless the user asked for them.
4. Do not "improve" unrelated code noticed along the way. Mention it separately as a suggestion; don't touch it.
5. Prefer the smallest diff that satisfies the request over a rewrite of the surrounding code.

## Hard stop conditions

Pause and ask before proceeding if any of these are true:

- The requested change conflicts with code you can actually see (not a hypothetical conflict).
- You cannot locate the code path being described — this is a signal the feature may not exist as described, not a cue to build a plausible version of it.
- Completing the request would require assuming business logic that isn't visible in the code or told to you directly.

## Why this matters here

End-of-project requests are usually small and precise. An agent that treats every request as a chance to "help more" by touching adjacent code is where unrequested, unverified changes creep in. This skill trades helpfulness-by-volume for helpfulness-by-precision.
