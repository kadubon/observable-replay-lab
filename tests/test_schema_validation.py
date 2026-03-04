from pathlib import Path

from experiments.reproduce import run_reproduce
from ref_impl.common import load_jsonl, load_schema, validate_instance, validate_log_events


def test_generated_artifacts_pass_schema_validation(tmp_path: Path):
    result = run_reproduce(seed=0, scenario="clean", results_dir=tmp_path)

    log_path = Path(result["artifacts"]["log_path"])
    events = load_jsonl(log_path)
    log_errors = validate_log_events(events)
    assert log_errors == []

    result_errors = validate_instance(result, load_schema("results.schema.json"))
    metric_errors = validate_instance(result["metrics"], load_schema("metrics.schema.json"))

    assert result_errors == []
    assert metric_errors == []
