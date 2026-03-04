# Minimal Example

Run a deterministic reproduction and inspect summary:

```bash
python -m cli.run reproduce --seed 0
python -m cli.run audit --seed 0
python -m cli.run summarize --seed 0 --scenario clean
```

Expected artifacts:

- `results/logs/clean_seed0.jsonl`
- `results/result_clean_seed0.json`
- `results/audit_report_seed0.json`

This example is designed to finish in minutes on a standard CPU.
