# AGENTS.md

## Purpose (Shortest Form)
Provide a deterministic, observable-only, no-meta MRI for replay-auditable growth/epistemics experiments.

## Inputs
- Scenario definition: `bench/scenarios.yaml`
- Fixed seed: CLI `--seed`
- Optional scenario selection: CLI `--scenario`

## Outputs
- JSONL logs: `results/logs/*.jsonl`
- Result JSON: `results/result_<scenario>_seed<seed>.json`
- Benchmark summary: `results/bench_summary_seed<seed>.json`
- Audit report: `results/audit_report_seed<seed>.json`
  - includes security checks for local path leakage and secret-like literals

## Primary Commands
- `python -m cli.run reproduce --seed 0`
- `python -m cli.run bench --seed 0`
- `python -m cli.run validate --seed 0`
- `python -m cli.run audit --seed 0`
- `python -m cli.run summarize --seed 0 --scenario clean`

## Deliverables in This Repo
- Specs: `spec/`
  - machine manifest: `spec/repo_manifest.json`
  - paper alignment map: `spec/paper_alignment.yaml`
- Schemas: `schemas/`
- Reference implementation: `ref_impl/`
- Benchmarks: `bench/`
- Reproducible experiments: `experiments/`
- Unified CLI: `cli/run.py`

## Extension Points
- Add scenarios in `bench/scenarios.yaml`
- Add new metrics in `spec/metrics.yaml` and `ref_impl/metrics.py`
- Extend gate logic in `ref_impl/ste_sim.py`
- Extend epistemics core in `ref_impl/mte_core.py`
- Tighten schemas in `schemas/*.json`
