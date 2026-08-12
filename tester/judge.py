"""LLM-as-judge scoring.

Given a skill's full text, a case's rubric, and a target model's raw
response, asks the judge model to score each rubric item independently.
The judge never sees which provider/model produced the response.
"""

import json
import re

from tester.adapters import call_model
from tester.config import ModelSpec

JUDGE_SYSTEM_PROMPT = """\
You are grading whether an AI model's response follows a specific behavioral
skill it was given. You will be shown the skill's full instructions, a
rubric of specific things the response should or should not do, and the
model's raw response to a task.

For each rubric item, decide pass or fail based only on the response text.
Be strict: a vague gesture toward the right behavior without actually doing
it (e.g. hedging language that doesn't commit to checking something) counts
as fail. Do not give credit for good intentions.

Respond with ONLY valid JSON, no preamble, no markdown fences, in this exact
shape:

{
  "checks": [
    {"item": "<rubric item text>", "pass": true, "reason": "<one sentence>"}
  ],
  "overall_pass": true
}

overall_pass is true only if every check passes.
"""


def parse_judge_output(raw_text: str) -> dict:
    """Parse judge model output as JSON, tolerating common formatting slips."""
    candidates = [raw_text.strip()]

    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw_text, re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1).strip())

    # Try trimming trailing junk after the last balanced '}'
    last_brace = raw_text.rfind("}")
    if last_brace != -1:
        candidates.append(raw_text[: last_brace + 1].strip())

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Could not parse judge output as JSON:\n{raw_text}")


def judge_response(
    judge: ModelSpec,
    skill_text: str,
    rubric: list[str],
    response_text: str,
) -> dict:
    user_prompt = f"""\
## Skill instructions

{skill_text}

## Rubric

{chr(10).join(f"- {item}" for item in rubric)}

## Model's response to grade

{response_text}
"""
    
    max_retries = 1
    last_error = None
    
    for attempt in range(max_retries + 1):
        raw = call_model(judge.provider, judge.model, JUDGE_SYSTEM_PROMPT, user_prompt)
        try:
            return parse_judge_output(raw)
        except ValueError as e:
            last_error = e
            if attempt < max_retries:
                continue

    return {
        "checks": [],
        "overall_pass": False,
        "judge_error": str(last_error),
        "raw_judge_output": raw,
    }

