from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ref_impl.common import set_global_seed, sha256_digest, sort_events
from ref_impl.mte_core import run_mte
from ref_impl.ste_sim import simulate_ste


def run_core(events: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
    set_global_seed(seed)
    ordered = sort_events(events)
    ste_result = simulate_ste(ordered)
    mte_result = run_mte(ordered)
    return {"ste": ste_result, "mte": mte_result}


def deterministic_replay(events: List[Dict[str, Any]], seed: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    primary = run_core(events, seed)
    replayed = run_core(events, seed)

    primary_hash = sha256_digest(primary)
    replay_hash = sha256_digest(replayed)

    replay_info = {
        "primary_hash": primary_hash,
        "replay_hash": replay_hash,
        "match": bool(primary_hash == replay_hash),
    }
    return primary, replay_info, replayed
