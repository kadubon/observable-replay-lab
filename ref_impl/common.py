from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"


def set_global_seed(seed: int) -> None:
    """Set all random seeds used in this repository."""
    random.seed(seed)
    np.random.seed(seed)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def to_repo_relative(path: Path) -> str:
    """Return a repo-root-based relative POSIX path when possible.

    For paths outside the repository root, this returns an explicit relative path
    (for example ../../tmp/...), avoiding absolute local paths in artifacts.
    """
    resolved = path.resolve()
    root_resolved = ROOT.resolve()
    try:
        return resolved.relative_to(root_resolved).as_posix()
    except ValueError:
        try:
            return Path(os.path.relpath(resolved, start=root_resolved)).as_posix()
        except ValueError:
            # Different drive on Windows: fallback to absolute as last resort.
            return resolved.as_posix()


def resolve_repo_path(path_value: str | Path) -> Path:
    """Resolve either a repo-relative path or an absolute path to a concrete Path."""
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return (ROOT / candidate).resolve()


def read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_json(path: Path) -> Dict[str, Any]:
    # Accept UTF-8 files with or without BOM for Windows-friendly portability.
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(to_builtin(data), handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_dumps(row))
            handle.write("\n")


def sort_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(events, key=lambda x: (int(x["timestep"]), str(x.get("event_id", ""))))


def assert_event_keys(events: List[Dict[str, Any]]) -> None:
    keys = [(int(event["timestep"]), str(event.get("event_id", ""))) for event in events]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate (timestep, event_id) pair detected")


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_builtin(v) for v in value]
    if isinstance(value, tuple):
        return [to_builtin(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def canonical_dumps(data: Any) -> str:
    return json.dumps(to_builtin(data), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_digest(data: Any) -> str:
    payload = canonical_dumps(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_schema(filename: str) -> Dict[str, Any]:
    return read_json(SCHEMAS_DIR / filename)


def validate_instance(instance: Any, schema: Dict[str, Any]) -> List[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda err: err.path)
    return [f"{list(err.path)}: {err.message}" for err in errors]


def validate_log_events(events: List[Dict[str, Any]]) -> List[str]:
    schema = load_schema("log_event.schema.json")
    errors: List[str] = []
    ordered = sort_events(events)
    assert_event_keys(ordered)
    for idx, event in enumerate(ordered):
        event_errors = validate_instance(event, schema)
        errors.extend([f"event[{idx}] {message}" for message in event_errors])
    return errors
