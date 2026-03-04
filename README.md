[![DOI](https://zenodo.org/badge/1172138352.svg)](https://doi.org/10.5281/zenodo.18856604)
Repository DOI: https://doi.org/10.5281/zenodo.18856604

# Observable Replay Lab (MRI)

This repository is a minimal reference implementation for **observable-only** and **no-meta** autonomous intelligence workflows with **evaluator-independence**, **deterministic replay**, and **reproducible audit** as first-class requirements. It packages a replayable **gate model** and metrology-driven **epistemics** pipeline with explicit **identifiability** and **uncertainty** checks, including **doubling time** and **phase transition** signals. The design prioritizes machine-readability, schema validation, and capture-resilience proxies for AI crawler discoverability and reuse.

## What This Repository Provides

- `spec/`: machine-readable technical specifications (STE gate, MTE epistemics, metrics, log format).
- `spec/repo_manifest.json`: machine-readable repository map for crawler entrypoint discovery.
- `spec/paper_alignment.yaml`: explicit proxy-level alignment map to the two TeX papers.
- `schemas/`: JSON Schema for JSONL log events, result JSON, and metrics JSON.
- `ref_impl/`: minimal deterministic Python implementation (STE simulator, MTE core, metrics, replay).
- `bench/`: fixed-seed benchmark scenario definitions and log generation.
- `experiments/`: one-command reproduction pipeline that writes validated results.
- `cli/`: single entrypoint with `reproduce`, `bench`, `validate`, `summarize`, `audit`.
- security checks in `audit`: absolute-path leakage scan, secret-pattern scan, and `.gitignore` coverage checks.

## 3-Minute Quickstart

```bash
python -m cli.run reproduce --seed 0
python -m cli.run validate --seed 0
python -m cli.run audit --seed 0
```

The first command writes `results/result_clean_seed0.json` and `results/logs/clean_seed0.jsonl`.
The second command validates JSON Schema compliance and deterministic replay hash consistency.
The third command writes `results/audit_report_seed0.json` with crawler-style quality/alignment checks.

## Required Commands

```bash
python -m cli.run reproduce --seed 0
python -m cli.run validate --seed 0
pytest -q
```

## Output Artifacts

- `results/logs/*.jsonl`: deterministic benchmark/event logs.
- `results/result_<scenario>_seed<seed>.json`: STE + MTE outputs and metrics.
- `results/bench_summary_seed<seed>.json`: aggregate benchmark summary.
- `results/audit_report_seed<seed>.json`: machine-readable audit report (discoverability, reproducibility, paper alignment).
- security section inside audit report: local-path leak status, secret-like token scan status, and ignore-rule completeness.

Result JSON includes:

- `ste.doubling_time`, `ste.regime_change_count`, `ste.critical_condition`
- `mte.identifiable`, `mte.condition_number`, `mte.uncertainty`, `mte.failure_flags`
- metrics: `evaluator_dependence`, `capture_sensitivity`, `replay_consistency`, `plural_feasibility`, `identifiability_margin`

## Paper Sources (in `paper/`)

Titles are extracted from the TeX source in this repository.

- Sovereign Takeoff Engine (STE): Observable-Only Supergrowth Laws for No-Meta Autonomous Intelligence  
  https://doi.org/10.5281/zenodo.18828900
- Metrology-Theoretic Epistemics Engine (MTE): Observable-Only Metrology for Long-Horizon Autonomous Intelligence  
  https://doi.org/10.5281/zenodo.18845340

## Known Limits

- This is a minimal reference model, not a high-fidelity scientific simulator.
- Metrics are explicit proxies; they are useful for reproducible comparison, not real-world ground truth.
- STE and MTE assumptions are intentionally simplified and may not transfer to operational deployments without re-calibration.
- Benchmark perturbations (missing/delayed/garbled) are synthetic stressors.
- Alignment to the papers is intentionally **proxy-level** and explicitly declared in `spec/paper_alignment.yaml`.
- Strict theorem-by-theorem equivalence to the two papers is **not** claimed by this MRI.

## Installation (Optional)

```bash
pip install -e .
```

## License

Apache-2.0. See `LICENSE`.
