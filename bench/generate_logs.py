from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import numpy as np

from ref_impl.common import ensure_dir, read_yaml, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO_FILE = ROOT / "bench" / "scenarios.yaml"


def load_scenarios(path: Path = DEFAULT_SCENARIO_FILE) -> Dict[str, Dict[str, Any]]:
    payload = read_yaml(path)
    return {entry["name"]: entry for entry in payload.get("scenarios", [])}


def _rng_for(seed: int, scenario_name: str) -> np.random.Generator:
    offset = sum(ord(ch) for ch in scenario_name)
    return np.random.default_rng(seed + (offset * 9973))


def generate_scenario_events(scenario_name: str, cfg: Mapping[str, Any], seed: int) -> List[Dict[str, Any]]:
    rng = _rng_for(seed, scenario_name)
    timesteps = int(cfg["timesteps"])

    base_signal = float(cfg["base_signal"])
    signal_slope = float(cfg["signal_slope"])
    seasonality = float(cfg["seasonality"])
    intervention_step = int(cfg["intervention_step"])
    intervention_boost = float(cfg["intervention_boost"])

    missing_prob = float(cfg["missing_prob"])
    delayed_prob = float(cfg["delayed_prob"])
    garbled_prob = float(cfg["garbled_prob"])
    external_label_prob = float(cfg.get("external_label_prob", 0.0))

    signal_noise_std = float(cfg["signal_noise_std"])
    target_noise_std = float(cfg["target_noise_std"])

    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    events: List[Dict[str, Any]] = []
    prev_true_signal = base_signal

    for t in range(timesteps):
        trend_signal = base_signal + signal_slope * t + seasonality * np.sin(t / 3.0)
        true_signal = trend_signal + (intervention_boost if t >= intervention_step else 0.0)

        observed_signal = true_signal + float(rng.normal(0.0, signal_noise_std))
        target = 0.55 * true_signal + 0.25 * prev_true_signal + float(rng.normal(0.0, target_noise_std))

        missing = bool(rng.random() < missing_prob)
        delayed = bool(rng.random() < delayed_prob)
        garbled = bool(rng.random() < garbled_prob)

        if garbled:
            observed_signal = 0.6 * observed_signal + 0.2

        external_label = bool(rng.random() < external_label_prob)

        event_type = "intervene" if t == intervention_step else "observe"
        if t == timesteps - 1:
            event_type = "checkpoint"

        event = {
            "event_id": f"{scenario_name}-{seed}-{t:04d}",
            "timestep": t,
            "timestamp": (start + timedelta(seconds=t)).isoformat().replace("+00:00", "Z"),
            "event_type": event_type,
            "observation": {
                "signal": float(round(observed_signal, 8)),
                "target": float(round(target, 8)),
                "quality": float(round(1.0 - (0.4 * int(missing) + 0.3 * int(delayed) + 0.3 * int(garbled)), 8)),
                "external_label": external_label,
            },
            "intervention": {
                "mode": "boost" if t >= intervention_step else "none",
                "strength": float(intervention_boost if t >= intervention_step else 0.0),
            },
            "noise_flags": {
                "missing": missing,
                "delayed": delayed,
                "garbled": garbled,
            },
            "provenance": {
                "scenario": scenario_name,
                "seed": int(seed),
            },
        }
        events.append(event)
        prev_true_signal = true_signal

    return events


def generate_logs(
    seed: int,
    output_dir: Path,
    scenario_names: Iterable[str] | None = None,
    scenario_file: Path = DEFAULT_SCENARIO_FILE,
) -> Dict[str, Path]:
    scenarios = load_scenarios(scenario_file)
    selected = list(scenario_names) if scenario_names else sorted(scenarios.keys())

    ensure_dir(output_dir)
    outputs: Dict[str, Path] = {}
    for name in selected:
        if name not in scenarios:
            raise KeyError(f"Unknown scenario: {name}")
        events = generate_scenario_events(name, scenarios[name], seed)
        out_path = output_dir / f"{name}_seed{seed}.jsonl"
        write_jsonl(out_path, events)
        outputs[name] = out_path

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic benchmark logs")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "logs")
    args = parser.parse_args()

    scenario_names = args.scenario if args.scenario else None
    outputs = generate_logs(seed=args.seed, output_dir=args.output_dir, scenario_names=scenario_names)
    for scenario, path in outputs.items():
        print(f"{scenario}: {path}")


if __name__ == "__main__":
    main()
