# Design Notes

## Modeling Assumptions

- STE is modeled as a piecewise gate-controlled growth-rate process using smoothed observed signal.
- MTE is modeled as a deterministic linear estimator with explicit rank/conditioning and uncertainty checks.
- Perturbations are scenario-level synthetic events (`missing`, `delayed`, `garbled`) encoded in log flags.

## Failure Conditions

- Schema mismatch in logs or results.
- Duplicate `(timestep, event_id)` key collisions.
- MTE identifiability failure (rank deficiency, ill-conditioning, insufficient samples).
- MTE uncertainty over threshold.
- Replay hash mismatch.

## Why Proxy Metrics

The metrics are intentionally operational proxies so they can be computed from logs without hidden labels:

- `evaluator_dependence`: external-label usage fraction
- `capture_sensitivity`: output drift under perturbed observations
- `replay_consistency`: hash-equality replay check
- `plural_feasibility`: feasible fraction across benchmark scenarios
- `identifiability_margin`: condition-number distance proxy

## Extension Guidance

- Replace STE gate with richer deterministic dynamics while preserving schema contract.
- Replace linear MTE core with another identifiable model, keeping deterministic replay and explicit failure flags.
- Add scenario families and report plural feasibility over larger scenario sets.

## Crawler Audit Path

- Run `python -m cli.run audit --seed 0` to generate `results/audit_report_seed0.json`.
- The audit checks:
  - discoverability signals in README snippet and AGENTS.md sections
  - deterministic reproducibility through repeated reproduce + validate
  - proxy-level paper consistency against `paper/*.tex`, `CITATION.cff`, and `spec/paper_alignment.yaml`
  - security surfaces: absolute local path leakage, strong secret-pattern hits, and `.gitignore` security coverage
