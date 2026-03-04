from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np

from ref_impl.common import assert_event_keys, sort_events

DEFAULT_STE_PARAMS: Dict[str, float] = {
    "base_rate": 0.04,
    "boosted_rate": 0.14,
    "gate_threshold": 0.65,
    "critical_kappa": 0.096,
    "smoothing_alpha": 0.30,
}


def simulate_ste(events: List[Dict[str, Any]], params: Dict[str, float] | None = None) -> Dict[str, Any]:
    cfg = dict(DEFAULT_STE_PARAMS)
    if params:
        cfg.update(params)

    ordered = sort_events(events)
    assert_event_keys(ordered)

    alpha = float(cfg["smoothing_alpha"])
    smoothed = None

    growth_rates: List[float] = []
    gate_states: List[int] = []
    regime_changes: List[int] = []

    for event in ordered:
        signal = float(event["observation"]["signal"])
        if smoothed is None:
            smoothed = signal
        else:
            smoothed = alpha * signal + (1.0 - alpha) * smoothed

        gate_state = int(smoothed >= float(cfg["gate_threshold"]))
        if gate_states and gate_state != gate_states[-1]:
            regime_changes.append(int(event["timestep"]))

        growth_rate = float(cfg["boosted_rate"] if gate_state == 1 else cfg["base_rate"])
        gate_states.append(gate_state)
        growth_rates.append(growth_rate)

    mean_growth_rate = float(np.mean(growth_rates)) if growth_rates else 0.0
    doubling_time = float(math.log(2.0) / mean_growth_rate) if mean_growth_rate > 0.0 else 1.0e12
    critical_condition = bool(
        mean_growth_rate >= float(cfg["critical_kappa"]) and len(regime_changes) > 0
    )

    return {
        "mean_growth_rate": mean_growth_rate,
        "final_gate_state": int(gate_states[-1]) if gate_states else 0,
        "doubling_time": doubling_time,
        "regime_change_count": int(len(regime_changes)),
        "critical_condition": critical_condition,
        "regime_change_steps": regime_changes,
        "growth_rate_series": growth_rates,
        "gate_state_series": gate_states,
    }
