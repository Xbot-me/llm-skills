"""CLI: run a skill's eval cases against one or more models and grade them.

Usage:
    python -m tester.runner --skill grounding-before-editing \
        --models anthropic:claude-sonnet-4-5,gemini:gemini-2.5-flash

    python -m tester.runner --all
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from tester.adapters import call_model
from tester.config import ModelSpec, default_models, judge_spec, key_available, parse_model_specs
from tester.judge import judge_response

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
REPORTS_DIR = ROOT / "reports"

console = Console()


def load_skill(skill_dir: Path) -> tuple[str, list[dict]]:
    skill_md = skill_dir / "SKILL.md"
    cases_yaml = skill_dir / "evals" / "cases.yaml"

    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md in {skill_dir}")

    skill_text = skill_md.read_text()
    
    cases = []
    if cases_yaml.exists():
        cases = yaml.safe_load(cases_yaml.read_text()) or []
        
    return skill_text, cases


def discover_skills() -> list[Path]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(p.parent for p in SKILLS_DIR.rglob("SKILL.md"))


def run_case(
    skill_name: str,
    skill_text: str,
    case: dict,
    model: ModelSpec,
    judge: ModelSpec,
) -> dict:
    case_id = case["id"]
    prompt = case["prompt"]
    rubric = case["rubric"]

    if not key_available(model.provider):
        return {
            "skill": skill_name,
            "case": case_id,
            "model": str(model),
            "skipped": True,
            "reason": f"No API key set for provider '{model.provider}'.",
        }

    try:
        response_text = call_model(model.provider, model.model, skill_text, prompt)
    except Exception as exc:  # noqa: BLE001 - surface any provider error into the report
        return {
            "skill": skill_name,
            "case": case_id,
            "model": str(model),
            "error": f"{type(exc).__name__}: {exc}",
        }

    judgment = judge_response(judge, skill_text, rubric, response_text)

    return {
        "skill": skill_name,
        "case": case_id,
        "model": str(model),
        "prompt": prompt,
        "response": response_text,
        "judgment": judgment,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="Skill folder name under skills/. Omit with --all.")
    parser.add_argument("--all", action="store_true", help="Run every skill under skills/.")
    parser.add_argument(
        "--models",
        help="Comma-separated provider:model list. Falls back to DEFAULT_MODELS in .env.",
    )
    args = parser.parse_args()

    if not args.skill and not args.all:
        parser.error("Pass --skill <name> or --all.")

    models = parse_model_specs(args.models) if args.models else default_models()
    judge = judge_spec()

    if args.all:
        skill_dirs = discover_skills()
        if not skill_dirs:
            console.print("[yellow]No skills found under skills/.[/yellow]")
            sys.exit(0)
    else:
        matches = [p.parent for p in SKILLS_DIR.rglob("SKILL.md") if p.parent.name == args.skill]
        if not matches:
            target = SKILLS_DIR / args.skill
            if (target / "SKILL.md").exists():
                skill_dirs = [target]
            else:
                parser.error(f"Skill '{args.skill}' not found in any category under skills/")
        else:
            skill_dirs = matches

    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    all_results = []

    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        skill_text, cases = load_skill(skill_dir)
        
        if not cases:
            console.print(f"\n[bold]{skill_name}[/bold] — [yellow]Skipped (no cases found)[/yellow]")
            continue
            
        console.print(f"\n[bold]{skill_name}[/bold] — {len(cases)} case(s), {len(models)} model(s)")

        out_dir = REPORTS_DIR / skill_name / run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        for case in cases:
            for model in models:
                result = run_case(skill_name, skill_text, case, model, judge)
                all_results.append(result)

                out_file = out_dir / f"{case['id']}__{model.slug}.json"
                out_file.write_text(json.dumps(result, indent=2))

    write_summary(all_results, run_id)


def write_summary(results: list[dict], run_id: str) -> None:
    table = Table(title=f"Run {run_id}")
    table.add_column("Skill")
    table.add_column("Case")
    table.add_column("Model")
    table.add_column("Result")

    summary_lines = [f"# Eval run {run_id}\n", "| Skill | Case | Model | Result |", "|---|---|---|---|"]

    for r in results:
        if r.get("skipped"):
            status = f"skipped ({r['reason']})"
        elif r.get("error"):
            status = f"error: {r['error']}"
        else:
            passed = r["judgment"].get("overall_pass")
            status = "✅ pass" if passed else "❌ fail"

        table.add_row(r["skill"], r["case"], r["model"], status)
        summary_lines.append(f"| {r['skill']} | {r['case']} | {r['model']} | {status} |")

    console.print(table)

    summary_path = REPORTS_DIR / "summary-latest.md"
    summary_path.write_text("\n".join(summary_lines) + "\n")
    console.print(f"\nFull transcripts in [cyan]reports/*/{run_id}/[/cyan], summary in [cyan]{summary_path}[/cyan]")


if __name__ == "__main__":
    main()
