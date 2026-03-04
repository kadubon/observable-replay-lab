from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.audit_repo import run_repo_audit, summarize_report
from experiments.reproduce import run_benchmark, run_reproduce, run_validate
from ref_impl.common import read_json, resolve_repo_path

ROOT = Path(__file__).resolve().parents[1]


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_reproduce(args: argparse.Namespace) -> int:
    result = run_reproduce(seed=args.seed, scenario=args.scenario, results_dir=args.results_dir)
    _print_json(
        {
            "run_id": result["run_id"],
            "result_path": result["artifacts"]["result_path"],
            "log_path": result["artifacts"]["log_path"],
            "ste": result["ste"],
            "mte": result["mte"],
            "metrics": result["metrics"],
        }
    )
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    summary = run_benchmark(seed=args.seed, results_dir=args.results_dir)
    _print_json(summary)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    report = run_validate(seed=args.seed, scenario=args.scenario, results_dir=args.results_dir)
    _print_json(report)
    return 0 if report["ok"] else 1


def cmd_summarize(args: argparse.Namespace) -> int:
    path = args.path
    if path is not None and "audit_report" in path.name:
        summary = summarize_report(resolve_repo_path(path))
        _print_json(summary)
        return 0

    if path is None:
        path = args.results_dir / f"result_{args.scenario}_seed{args.seed}.json"

    payload = read_json(resolve_repo_path(path))
    summary = {
        "run_id": payload["run_id"],
        "scenario": payload["scenario"],
        "seed": payload["seed"],
        "doubling_time": payload["ste"]["doubling_time"],
        "critical_condition": payload["ste"]["critical_condition"],
        "identifiable": payload["mte"]["identifiable"],
        "uncertainty": payload["mte"]["uncertainty"],
        "failure_flags": payload["mte"]["failure_flags"],
        "metrics": payload["metrics"],
    }
    _print_json(summary)
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    report = run_repo_audit(seed=args.seed, scenario=args.scenario)
    _print_json(report)
    return 0 if report["status"] == "pass" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Observable replay lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reproduce_parser = subparsers.add_parser("reproduce", help="Run deterministic reproduction")
    reproduce_parser.add_argument("--seed", type=int, default=0)
    reproduce_parser.add_argument("--scenario", type=str, default="clean")
    reproduce_parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    reproduce_parser.set_defaults(func=cmd_reproduce)

    bench_parser = subparsers.add_parser("bench", help="Run benchmark across all scenarios")
    bench_parser.add_argument("--seed", type=int, default=0)
    bench_parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    bench_parser.set_defaults(func=cmd_bench)

    validate_parser = subparsers.add_parser("validate", help="Validate schemas and determinism")
    validate_parser.add_argument("--seed", type=int, default=0)
    validate_parser.add_argument("--scenario", type=str, default="clean")
    validate_parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    validate_parser.set_defaults(func=cmd_validate)

    summarize_parser = subparsers.add_parser("summarize", help="Summarize one result JSON")
    summarize_parser.add_argument("--seed", type=int, default=0)
    summarize_parser.add_argument("--scenario", type=str, default="clean")
    summarize_parser.add_argument("--path", type=Path, default=None)
    summarize_parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    summarize_parser.set_defaults(func=cmd_summarize)

    audit_parser = subparsers.add_parser("audit", help="Run crawler-style repository audit")
    audit_parser.add_argument("--seed", type=int, default=0)
    audit_parser.add_argument("--scenario", type=str, default="clean")
    audit_parser.set_defaults(func=cmd_audit)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
