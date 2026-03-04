from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from ref_impl.common import assert_event_keys, sort_events

DEFAULT_MTE_PARAMS: Dict[str, float] = {
    "cond_threshold": 1_000_000.0,
    "uncertainty_threshold": 0.25,
    "min_samples": 8,
    "delay_penalty": 0.03,
}


def _build_design_matrix(events: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    ordered = sort_events(events)
    assert_event_keys(ordered)

    rows: List[List[float]] = []
    targets: List[float] = []

    missing_count = 0
    delayed_count = 0
    garbled_count = 0
    prev_signal = None

    for event in ordered:
        obs = event["observation"]
        flags = event["noise_flags"]

        signal = float(obs["signal"])
        target = float(obs["target"])
        missing = bool(flags.get("missing", False))
        delayed = bool(flags.get("delayed", False))
        garbled = bool(flags.get("garbled", False))

        if missing:
            missing_count += 1
            prev_signal = signal
            continue

        model_signal = prev_signal if delayed and prev_signal is not None else signal
        lagged_signal = prev_signal if prev_signal is not None else model_signal

        if delayed:
            delayed_count += 1
        if garbled:
            model_signal = 0.5 * model_signal
            garbled_count += 1

        rows.append([1.0, float(model_signal), float(lagged_signal)])
        targets.append(target)
        prev_signal = signal

    total = max(len(ordered), 1)
    stats = {
        "missing_fraction": float(missing_count) / float(total),
        "delayed_fraction": float(delayed_count) / float(total),
        "garbled_fraction": float(garbled_count) / float(total),
    }

    if not rows:
        return np.zeros((0, 3), dtype=np.float64), np.zeros((0,), dtype=np.float64), stats

    return np.array(rows, dtype=np.float64), np.array(targets, dtype=np.float64), stats


def run_mte(events: List[Dict[str, Any]], params: Dict[str, float] | None = None) -> Dict[str, Any]:
    cfg = dict(DEFAULT_MTE_PARAMS)
    if params:
        cfg.update(params)

    x, y, stats = _build_design_matrix(events)

    n_samples = int(x.shape[0])
    n_features = int(x.shape[1]) if x.ndim == 2 else 0

    failure_flags: List[str] = []
    if n_samples == 0:
        return {
            "identifiable": False,
            "rank": 0,
            "condition_number": 1.0e12,
            "uncertainty": 1.0,
            "failure_flags": ["no_usable_samples"],
            "coefficients": [0.0, 0.0, 0.0],
            "sample_count": 0,
            **stats,
        }

    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    rank = int(np.linalg.matrix_rank(x))

    try:
        xtx = x.T @ x
        condition_number = float(np.linalg.cond(xtx)) if rank == n_features else 1.0e12
    except np.linalg.LinAlgError:
        condition_number = 1.0e12

    residual = y - (x @ beta)
    residual_variance = float(np.mean(residual ** 2)) if residual.size > 0 else 1.0

    uncertainty = (
        residual_variance
        + float(cfg["delay_penalty"]) * float(stats["delayed_fraction"])
        + 0.05 * float(stats["missing_fraction"])
        + 0.05 * float(stats["garbled_fraction"])
    )

    identifiable = bool(
        n_samples >= int(cfg["min_samples"])
        and rank == n_features
        and condition_number <= float(cfg["cond_threshold"])
    )

    if n_samples < int(cfg["min_samples"]):
        failure_flags.append("insufficient_samples")
    if rank < n_features:
        failure_flags.append("rank_deficient")
    if condition_number > float(cfg["cond_threshold"]):
        failure_flags.append("ill_conditioned")
    if uncertainty > float(cfg["uncertainty_threshold"]):
        failure_flags.append("high_uncertainty")

    return {
        "identifiable": identifiable,
        "rank": rank,
        "condition_number": condition_number,
        "uncertainty": float(uncertainty),
        "failure_flags": failure_flags,
        "coefficients": [float(v) for v in beta.tolist()],
        "sample_count": n_samples,
        **stats,
    }
