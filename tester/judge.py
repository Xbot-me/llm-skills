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


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


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
    raw = call_model(judge.provider, judge.model, JUDGE_SYSTEM_PROMPT, user_prompt)
    try:
        return _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        return {
            "checks": [],
            "overall_pass": False,
            "judge_error": "Could not parse judge output as JSON.",
            "raw_judge_output": raw,
        }
