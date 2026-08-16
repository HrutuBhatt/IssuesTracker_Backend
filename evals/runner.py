"""
Eval runner — seed fixtures, run all eval categories, print scorecard.

Usage (from backend/ directory):
    python -m evals.runner
"""

import sys
import os

# Allow imports from backend/app/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.db.database import SessionLocal
from app.models.models import ProjectRole
from app.services.assistant_client import get_assistant_client
from app.services.assistant_service import AssistantService
from app.services.guardrails import GuardrailService

from evals.fixtures import seed, teardown, FixtureData
from evals.test_cases import (
    GUARDRAIL_INPUT_CASES, TRAJECTORY_CASES, GEVAL_CASES, RULE_CASES,
)
from evals.metrics.trajectory import check_trajectory
from evals.metrics.g_eval import g_eval
from evals.metrics.classification import compute_metrics
from evals.metrics.rule_based import (
    check_issues_modified,
    check_no_system_prompt_leak,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run_agent(fx: FixtureData, prompt: str, actor_role: ProjectRole):
    """Run the agent and return (reply, issues_modified, trajectory)."""
    db = SessionLocal()
    try:
        client = get_assistant_client()
        service = AssistantService(client, db)
        actor_id = {
            ProjectRole.ADMIN:     fx.admin_id,
            ProjectRole.DEVELOPER: fx.dev1_id,
            ProjectRole.CLIENT:    fx.client_id,
        }[actor_role]
        return service.run_agent(
            prompt=prompt,
            project_id=fx.project_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
    finally:
        db.close()


def _tick(passed: bool) -> str:
    return "✓" if passed else "✗"


def _print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ── Category runners ───────────────────────────────────────────────────────────

def run_guardrail_evals(fx: FixtureData) -> dict:
    _print_section("GUARDRAIL INPUT")
    db = SessionLocal()
    client = get_assistant_client()
    guardrail = GuardrailService(client.groq)
    db.close()

    predictions, labels = [], []
    for case in GUARDRAIL_INPUT_CASES:
        is_safe, reason = guardrail.check_input(case.prompt)
        passed = is_safe == case.expected_safe
        predictions.append(is_safe)
        labels.append(case.expected_safe)
        status = "PASS" if passed else f"FAIL (got safe={is_safe}, reason: {reason})"
        print(f"  {_tick(passed)} {case.name:<45} {status}")

    metrics = compute_metrics(predictions, labels)
    print(f"\n  Precision: {metrics['precision']} | Recall: {metrics['recall']} | F1: {metrics['f1']} | Accuracy: {metrics['accuracy']}")
    passed_count = sum(p == l for p, l in zip(predictions, labels))
    return {"passed": passed_count, "total": len(GUARDRAIL_INPUT_CASES), "metrics": metrics}


def run_trajectory_evals(fx: FixtureData) -> dict:
    _print_section("TRAJECTORY")
    passed_count = 0
    for case in TRAJECTORY_CASES:
        reply, issues_modified, trajectory = _run_agent(fx, case.prompt, case.actor_role)
        passed, reason = check_trajectory(trajectory, case.rules)
        if passed:
            passed_count += 1
        status = "PASS" if passed else f"FAIL ({reason})"
        print(f"  {_tick(passed)} {case.name:<45} {status}")
        print(f"       trajectory: {[c['name'] for c in trajectory]}")
    return {"passed": passed_count, "total": len(TRAJECTORY_CASES)}


def run_geval_evals(fx: FixtureData) -> dict:
    _print_section("G-EVAL (LLM-as-judge)")
    client = get_assistant_client()
    passed_count = 0
    for case in GEVAL_CASES:
        reply, _, _ = _run_agent(fx, case.prompt, case.actor_role)
        score, reasoning = g_eval(case.prompt, reply, case.criteria, client.groq)
        passed = score >= case.min_score
        if passed:
            passed_count += 1
        status = "PASS" if passed else f"FAIL (score {score} < min {case.min_score})"
        print(f"  {_tick(passed)} {case.name:<45} score={score}/5  {status}")
        print(f"       {reasoning}")
    return {"passed": passed_count, "total": len(GEVAL_CASES)}


def run_rule_evals(fx: FixtureData) -> dict:
    _print_section("RULE-BASED")
    passed_count = 0
    total = 0
    for case in RULE_CASES:
        reply, issues_modified, _ = _run_agent(fx, case.prompt, case.actor_role)
        case_passed = True
        for chk in case.checks:
            total += 1
            if chk["type"] == "issues_modified":
                ok, reason = check_issues_modified(issues_modified, chk["expected"])
            elif chk["type"] == "no_leak":
                ok, reason = check_no_system_prompt_leak(reply)
            else:
                ok, reason = False, f"unknown check type: {chk['type']}"

            if not ok:
                case_passed = False
            status = "PASS" if ok else f"FAIL ({reason})"
            print(f"  {_tick(ok)} {case.name} / {chk['name']:<35} {status}")

        if case_passed:
            passed_count += 1

    return {"passed": passed_count, "total": len(RULE_CASES)}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  EVAL RUNNER — Issue Tracking AI Assistant")
    print("=" * 60)

    db = SessionLocal()
    print("\n[Setup] Seeding test fixtures...")
    fx = seed(db)
    db.close()
    print(f"  Project ID: {fx.project_id} | Admin: {fx.admin_id} | Dev1: {fx.dev1_id} | Dev2: {fx.dev2_id}")

    results = {}
    try:
        results["guardrail"] = run_guardrail_evals(fx)
        results["trajectory"] = run_trajectory_evals(fx)
        results["g_eval"]     = run_geval_evals(fx)
        results["rule"]       = run_rule_evals(fx)
    finally:
        db = SessionLocal()
        print("\n[Teardown] Removing test fixtures...")
        teardown(db, fx)
        db.close()
        print("  Done.")

    # ── Scorecard ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SCORECARD")
    print("=" * 60)
    total_passed = total_cases = 0
    labels = {
        "guardrail":  "Guardrail Input",
        "trajectory": "Trajectory",
        "g_eval":     "G-Eval",
        "rule":       "Rule-based",
    }
    for key, r in results.items():
        p, t = r["passed"], r["total"]
        total_passed += p
        total_cases  += t
        pct = int(p / t * 100) if t else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        print(f"  {labels[key]:<20} {bar}  {p}/{t} ({pct}%)")
        if key == "guardrail" and "metrics" in r:
            m = r["metrics"]
            print(f"  {'':20}  Precision={m['precision']} Recall={m['recall']} F1={m['f1']}")

    overall_pct = int(total_passed / total_cases * 100) if total_cases else 0
    print(f"\n  {'OVERALL':<20} {total_passed}/{total_cases} ({overall_pct}%)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
