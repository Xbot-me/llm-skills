# llm-skills

A repo for authoring `SKILL.md` files and testing whether they actually change
model behavior — across providers, not just one.

The `SKILL.md` format here follows the open agent-skills standard (the same
format Antigravity, Claude, and others read): a folder with a YAML-fronted
`SKILL.md`. This repo adds one thing on top: an `evals/` folder per skill and
a harness that runs those evals against multiple model providers and grades
the output.

## Why

A skill can read well and still fail silently on a real model — it might
follow the rule on Claude and ignore it on Gemini, or follow it for the
example in the description and not for a slightly different phrasing. This
repo exists to catch that before the skill goes into a real project.

## Leaderboard

<!-- LEADERBOARD_START -->
| Skill | Case | Model | Result |
|---|---|---|---|
<!-- LEADERBOARD_END -->

## Structure

```
llm-skills/
├── skills/
│   ├── coding/
│   │   ├── grounding-before-editing/
│   │   └── <skill-name>/
│   │       ├── SKILL.md              # the skill itself
│   │       └── evals/
│   │           └── cases.yaml        # scenarios to test it against
│   └── writing/
│       └── humanizer/
├── tester/
│   ├── adapters.py                # unified call interface per provider
│   ├── judge.py                   # LLM-as-judge scoring
│   ├── runner.py                  # CLI entrypoint
│   └── config.py
├── reports/                       # generated per run, gitignored by default
├── .github/workflows/eval.yml     # manual-trigger CI (see note below)
├── requirements.txt
└── .env.example
```

## Adding a skill

1. `skills/<category>/<name>/SKILL.md` — same format as any Antigravity/Claude skill:
   YAML frontmatter (`name`, `description`) plus instructions.
2. `skills/<category>/<name>/evals/cases.yaml` — a list of scenarios. Each case is:

```yaml
- id: short-id
  prompt: |
    The full scenario given to the model, as if a user or an agent
    context handed it this task. Include enough setup that the model
    has to choose between following the skill and taking a shortcut.
  rubric:
    - A specific, checkable behavior the skill should produce.
    - Another one. Keep each item to a single observable thing.
```

Write rubric items as things a human reviewer could check in the output
without needing to run code — the judge model does exactly that, nothing more.

## Running evals

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the keys for whichever providers you're testing
python -m tester.runner --skill grounding-before-editing \
    --models anthropic:claude-sonnet-4-5,gemini:gemini-2.5-flash,groq:llama-3.3-70b-versatile
```

Check `docs.claude.com`, `ai.google.dev`, and `console.groq.com/docs/models`
for current model IDs before running — these change often enough that
hardcoding one here would go stale.

Omit `--skill` to run every skill in `skills/`. Omit `--models` to use the
default in `.env` (`DEFAULT_MODELS`).

Output goes to `reports/<skill>/<run-timestamp>/`:
- one JSON transcript + judgment per (case, model) pair
- a `summary.md` table: skill × model × case, pass/fail, judge notes

## The judge

By default the judge is a separate call to an Anthropic model (configurable
via `JUDGE_PROVIDER` / `JUDGE_MODEL` in `.env`) — it's given the skill's full
text, the case's rubric, and the target model's raw response, and asked to
score each rubric item as pass/fail with a one-line reason. It never sees
which provider generated the response, to avoid provider bias in grading.

This is a judgment call, not a proof — treat a "pass" as "a careful reader
would say this followed the rule," not as a formal guarantee. For anything
load-bearing, read the actual transcripts in `reports/`, don't just trust the
aggregate score.

## CI

`.github/workflows/eval.yml` is set to `workflow_dispatch` only (manual
trigger), not on every push. Running the full eval suite means real API
calls across three providers — that shouldn't happen automatically on every
commit and quietly burn budget. Add your provider keys as repo secrets, then
trigger it manually or on a schedule if you want regression checks over time.

## Roadmap ideas (not built yet)

- A "grounding" eval mode that actually spins up a scratch repo and lets the
  target model run real tool calls, instead of describing a scenario in text.
  This is the honest next step if text-only evals stop catching real
  regressions.
- Multi-turn cases (skill tested across a longer conversation, not one shot).
- A regression baseline so a skill edit shows a diff in pass rate, not just
  a fresh run.
