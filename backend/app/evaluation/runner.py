"""
Evaluation runner for the LangGraph agents (Developer 4).

Runs each agent node over its dataset, applies deterministic ground-truth
checks, and reports an aggregate quality score. Requires GEMINI_API_KEY (the
agents make real Gemini calls); LangSmith tracing is automatic if configured.

Run from the backend/ directory:
    python -m app.evaluation.runner --agent hypothesis
    python -m app.evaluation.runner --all
    python -m app.evaluation.runner --all --output eval_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Callable

from app.agents import context_agent, experiment_design_agent, hypothesis_agent
from app.evaluation.datasets import get_dataset, get_dataset_names
from app.evaluation.ground_truth import CHECKS, OUTPUT_KEY, aggregate_scores

# agent name -> node function
_NODES: dict[str, Callable[[dict], dict]] = {
    "context": context_agent.node,
    "hypothesis": hypothesis_agent.node,
    "experiment_design": experiment_design_agent.node,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_agent_eval(agent_name: str) -> dict[str, Any]:
    """Run ground-truth evaluation for a single agent."""
    print(f"\n{'=' * 60}\n  Evaluating: {agent_name}\n{'=' * 60}\n")
    dataset = get_dataset(agent_name)
    node = _NODES[agent_name]
    check_fn = CHECKS[agent_name]
    out_key = OUTPUT_KEY[agent_name]

    results = []
    for i, example in enumerate(dataset):
        print(f"  [{i + 1}/{len(dataset)}] running node...")
        update = node(dict(example["input"]))
        if "errors" in update and out_key not in update:
            print(f"       [ERROR] {update['errors']}")
            results.append({"index": i, "error": update["errors"],
                            "result": {"score": 0.0, "checks": {}, "passed": 0, "total": 0}})
            continue
        output = update.get(out_key, {})
        gt = check_fn(output, example.get("expected", {}))
        results.append({"index": i, "output": output, "result": gt})
        mark = "PASS" if gt["score"] >= 0.7 else "WARN" if gt["score"] >= 0.5 else "FAIL"
        print(f"       [{mark}] score={gt['score']} ({gt['passed']}/{gt['total']})")

    aggregate = aggregate_scores([r["result"] for r in results])
    print(f"\n  Aggregate: avg={aggregate['avg_score']} "
          f"min={aggregate['min_score']} max={aggregate['max_score']}")
    return {"agent": agent_name, "timestamp": _now(), "results": results, "aggregate": aggregate}


def run_all() -> dict[str, Any]:
    all_results = {name: run_agent_eval(name) for name in get_dataset_names()}
    print(f"\n{'=' * 60}\n  SUMMARY\n{'=' * 60}")
    all_pass = True
    for name, res in all_results.items():
        avg = res["aggregate"]["avg_score"]
        all_pass = all_pass and avg >= 0.7
        print(f"  {name}: {'PASS' if avg >= 0.7 else 'FAIL'} (avg={avg})")
    print(f"\n  Overall: {'ALL PASSED' if all_pass else 'SOME BELOW 0.7'}")
    return {"timestamp": _now(), "results": all_results, "all_passed": all_pass}


def generate_quality_report(results: dict[str, Any]) -> str:
    lines = ["# AI Quality Report", f"\n- Generated: {_now()}", "\n| Agent | Avg | Min | Max | N |",
             "|-------|-----|-----|-----|---|"]
    agents = results.get("results", {})
    if "aggregate" in results:  # single-agent result
        agents = {results["agent"]: results}
    for name, res in agents.items():
        a = res["aggregate"]
        lines.append(f"| {name} | {a['avg_score']} | {a['min_score']} | {a['max_score']} | {a['count']} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the LangGraph agents")
    parser.add_argument("--agent", choices=get_dataset_names())
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", help="Write results to this JSON file")
    args = parser.parse_args()

    if args.all:
        results = run_all()
    elif args.agent:
        results = run_agent_eval(args.agent)
    else:
        parser.print_help()
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n  Results saved to {args.output}")

    print("\n" + generate_quality_report(results))


if __name__ == "__main__":
    main()
