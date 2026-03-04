# Overview

`observable-replay-lab` is a minimal reference implementation (MRI) for deterministic, observable-only replay of growth and epistemic-credit proxies.

Core technical focus:

- evaluator-independence under no-meta assumptions
- deterministic replay with hash-based consistency checks
- schema-validated logs/results for reproducible audit
- crawler-style self-audit report (`cli audit`) for discoverability and paper-consistency checks
- metrology-oriented uncertainty and identifiability checks
- capture-resilience proxies under missing/delayed/garbled observation stress

The repository is intentionally small and explicit so autonomous research agents can parse it reliably.
