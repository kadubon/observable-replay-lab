from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from bench.generate_logs import generate_logs, generate_scenario_events, load_scenarios
from ref_impl.common import (
    ensure_dir,
    load_jsonl,
    load_schema,
    resolve_repo_path,
    to_repo_relative,
    validate_instance,
    validate_log_events,
    write_json,
)
from ref_impl.metrics import compute_metrics
from ref_impl.replay import deterministic_replay, run_core
from ref_impl.ste_sim import simulate_ste

ROOT = Path(__file__).resolve().parents[1]


def _ste_payload(ste_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mean_growth_rate": float(ste_result["mean_growth_rate"]),
        "final_gate_state": int(ste_result["final_gate_state"]),
        "doubling_time": float(ste_result["doubling_time"]),
        "regime_change_count": int(ste_result["regime_change_count"]),
        "critical_condition": bool(ste_result["critical_condition"]),
    }


def _mte_payload(mte_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "identifiable": bool(mte_result["identifiable"]),
        "rank": int(mte_result["rank"]),
        "condition_number": float(mte_result["condition_number"]),
        "uncertainty": float(mte_result["uncertainty"]),
        "failure_flags": list(mte_result["failure_flags"]),
        "coefficients": [float(v) for v in mte_result["coefficients"]],
    }


def _plural_flags(seed: int) -> List[bool]:
    scenarios = load_scenarios()
    flags: List[bool] = []
    for name, cfg in scenarios.items():
        events = generate_scenario_events(name, cfg, seed)
        core = run_core(events, seed)
        flags.append(bool(core["ste"]["critical_condition"]) and len(core["mte"]["failure_flags"]) == 0)
    return flags


def run_reproduce(seed: int = 0, scenario: str = "clean", results_dir: Path | None = None) -> Dict[str, Any]:
    target_dir = ensure_dir(results_dir or (ROOT / "results"))
    logs_dir = ensure_dir(target_dir / "logs")

    scenarios = load_scenarios()
    if scenario not in scenarios:
        raise KeyError(f"Unknown scenario '{scenario}'. Available: {sorted(scenarios)}")

    outputs = generate_logs(seed=seed, output_dir=logs_dir, scenario_names=[scenario])
    log_path = outputs[scenario]

    events = load_jsonl(log_path)
    log_errors = validate_log_events(events)
    if log_errors:
        raise ValueError("Log validation failed: " + " | ".join(log_errors))

    primary, replay_info, _ = deterministic_replay(events, seed)

    clean_events = generate_scenario_events("clean", scenarios["clean"], seed)
    clean_ste = simulate_ste(clean_events)
    feasible_flags = _plural_flags(seed)

    metrics = compute_metrics(
        events=events,
        clean_doubling=float(clean_ste["doubling_time"]),
        observed_doubling=float(primary["ste"]["doubling_time"]),
        mte_result=primary["mte"],
        primary_hash=str(replay_info["primary_hash"]),
        replay_hash=str(replay_info["replay_hash"]),
        feasible_flags=feasible_flags,
    )

    result_path = target_dir / f"result_{scenario}_seed{seed}.json"
    result: Dict[str, Any] = {
        "run_id": f"{scenario}-seed-{seed}",
        "seed": int(seed),
        "scenario": scenario,
        "ste": _ste_payload(primary["ste"]),
        "mte": _mte_payload(primary["mte"]),
        "metrics": metrics,
        "replay": {
            "primary_hash": str(replay_info["primary_hash"]),
            "replay_hash": str(replay_info["replay_hash"]),
            "match": bool(replay_info["match"]),
        },
        "artifacts": {
            "log_path": to_repo_relative(log_path),
            "result_path": to_repo_relative(result_path),
        },
    }

    metrics_errors = validate_instance(metrics, load_schema("metrics.schema.json"))
    result_errors = validate_instance(result, load_schema("results.schema.json"))
    if metrics_errors or result_errors:
        merged = metrics_errors + result_errors
        raise ValueError("Result validation failed: " + " | ".join(merged))

    write_json(result_path, result)
    return result


def run_validate(seed: int = 0, scenario: str = "clean", results_dir: Path | None = None) -> Dict[str, Any]:
    target_dir = ensure_dir(results_dir or (ROOT / "results"))
    result = run_reproduce(seed=seed, scenario=scenario, results_dir=target_dir)

    events = load_jsonl(resolve_repo_path(result["artifacts"]["log_path"]))
    log_errors = validate_log_events(events)
    result_errors = validate_instance(result, load_schema("results.schema.json"))
    metric_errors = validate_instance(result["metrics"], load_schema("metrics.schema.json"))

    _, replay_info, _ = deterministic_replay(events, seed)
    replay_ok = (
        replay_info["match"]
        and replay_info["primary_hash"] == result["replay"]["primary_hash"]
        and replay_info["replay_hash"] == result["replay"]["replay_hash"]
    )

    errors = []
    errors.extend(log_errors)
    errors.extend(result_errors)
    errors.extend(metric_errors)
    if not replay_ok:
        errors.append("determinism_mismatch")

    return {
        "ok": len(errors) == 0,
        "seed": int(seed),
        "scenario": scenario,
        "errors": errors,
        "result_path": result["artifacts"]["result_path"],
    }


def run_benchmark(seed: int = 0, results_dir: Path | None = None) -> Dict[str, Any]:
    target_dir = ensure_dir(results_dir or (ROOT / "results"))
    scenarios = sorted(load_scenarios().keys())

    runs: List[Dict[str, Any]] = []
    for scenario in scenarios:
        result = run_reproduce(seed=seed, scenario=scenario, results_dir=target_dir)
        runs.append(
            {
                "scenario": scenario,
                "result_path": result["artifacts"]["result_path"],
                "critical_condition": result["ste"]["critical_condition"],
                "failure_flags": result["mte"]["failure_flags"],
                "metrics": result["metrics"],
            }
        )

    summary = {
        "seed": int(seed),
        "scenario_count": len(runs),
        "runs": runs,
    }
    summary_path = target_dir / f"bench_summary_seed{seed}.json"
    write_json(summary_path, summary)
    summary["summary_path"] = to_repo_relative(summary_path)
    return summary
