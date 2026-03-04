# Glossary

This glossary pins minimal technical meanings used by the MRI implementation.

- **no-meta**: No privileged external evaluator is assumed during execution; decisions are derived from observable artifacts only.
- **observable-only**: Every credited claim is a deterministic function of logged, replayable events.
- **replay**: Re-execution of the same log stream with pinned parameters and seed produces byte-identical outputs.
- **audit**: Post-hoc machine validation of logs, outputs, and metrics against JSON Schema plus deterministic replay checks.
- **gate**: Deterministic predicate that switches model regime (for STE) or pass/fail credit conditions (for MTE).
- **metrology**: Quantification discipline for uncertainty, calibration assumptions, and measurement failure surfaces.
- **identifiability**: Whether model parameters are estimable from available observations under rank/conditioning constraints.
- **evaluator-independence**: Operational property where result computation avoids privileged external judge channels.
- **capture-resilience**: Robustness proxy under missing/delayed/garbled observation corruption.
- **pluralistic autonomy**: Feasibility across multiple scenario families rather than a single environment assumption.
