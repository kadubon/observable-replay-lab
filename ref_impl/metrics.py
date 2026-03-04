from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def evaluator_dependence(events: List[Dict[str, Any]]) -> float:
    if not events:
        return 0.0
    external_refs = 0
    for event in events:
        external_refs += int(bool(event.get("observation", {}).get("external_label", False)))
    return _clip01(external_refs / float(len(events)))


def capture_sensitivity(clean_doubling: float, observed_doubling: float) -> float:
    denominator = max(abs(float(clean_doubling)), 1.0e-9)
    delta = abs(float(clean_doubling) - float(observed_doubling)) / denominator
    return _clip01(delta)


def replay_consistency(primary_hash: str, replay_hash: str) -> float:
    return 1.0 if str(primary_hash) == str(replay_hash) else 0.0


def plural_feasibility(feasible_flags: Iterable[bool]) -> float:
    flags = list(feasible_flags)
    if not flags:
        return 0.0
    return _clip01(sum(int(bool(v)) for v in flags) / float(len(flags)))


def identifiability_margin(identifiable: bool, condition_number: float) -> float:
    if not identifiable:
        return 0.0
    value = 1.0 - math.log10(float(condition_number) + 1.0) / 6.0
    return _clip01(value)


def compute_metrics(
    events: List[Dict[str, Any]],
    clean_doubling: float,
    observed_doubling: float,
    mte_result: Dict[str, Any],
    primary_hash: str,
    replay_hash: str,
    feasible_flags: Iterable[bool],
) -> Dict[str, float]:
    return {
        "evaluator_dependence": evaluator_dependence(events),
        "capture_sensitivity": capture_sensitivity(clean_doubling, observed_doubling),
        "replay_consistency": replay_consistency(primary_hash, replay_hash),
        "plural_feasibility": plural_feasibility(feasible_flags),
        "identifiability_margin": identifiability_margin(
            bool(mte_result.get("identifiable", False)),
            float(mte_result.get("condition_number", 1.0e12)),
        ),
    }
