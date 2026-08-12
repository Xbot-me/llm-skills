---
name: grounding-before-editing
description: >
  Forces the agent to read a file's actual current contents before
  editing, describing, or referencing it — instead of relying on
  earlier conversation context, memory, or assumptions. Use before
  any file edit, and especially when returning to a project after
  a gap or late in a project when files have likely drifted from
  what was last discussed.
---

# Grounding Before Editing

**Rule: never edit, describe, or reference a file's contents without reading its current state on disk in this turn.**

## Checklist

- [ ] Read the target file(s) fresh. Do not rely on an earlier summary, a memory of what "should" be there, or how a similar file usually looks.
- [ ] If the file doesn't exist, say so explicitly. Do NOT invent plausible-looking content for a missing file or path.
- [ ] Before calling a function, using an API, or referencing a variable/config key, search the codebase to confirm it actually exists there. Do not assume it exists because it's common in similar projects.
- [ ] If unsure whether something exists, say "I need to check X" and go check it — never assert as fact.
- [ ] When a request references "the function that does X" or similar, locate it by search first. Never guess a name and proceed as if it were confirmed.

## Anti-patterns to catch and stop

- Writing code that calls a function/endpoint/prop not confirmed to exist in this codebase.
- Describing a file's structure from memory of an earlier phase of the conversation rather than the file as it is now.
- Assuming a config key, env var, or column name without checking the actual config/schema file.
- Filling gaps in an incomplete read with "typical" boilerplate instead of saying the read was incomplete.

## Why this matters here

Most fabrication happens at the seam between "what I remember about this project" and "what's actually in it right now." This skill closes that seam by making a fresh read mandatory, not optional, before any claim or edit.
