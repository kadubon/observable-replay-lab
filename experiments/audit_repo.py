from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from experiments.reproduce import run_benchmark, run_reproduce, run_validate
from ref_impl.common import (
    ensure_dir,
    load_schema,
    read_json,
    read_yaml,
    to_repo_relative,
    validate_instance,
    write_json,
)

ROOT = Path(__file__).resolve().parents[1]

SNIPPET_KEYWORDS = [
    "observable-only",
    "no-meta",
    "evaluator-independence",
    "deterministic replay",
    "reproducible audit",
    "metrology",
    "epistemics",
    "identifiability",
    "uncertainty",
    "gate model",
    "phase transition",
    "doubling time",
    "capture-resilience",
]

EXPECTED_PAPERS = [
    {
        "id": "ste_2026",
        "tex_path": ROOT / "paper" / "Sovereign Takeoff Engine.tex",
        "title": "Sovereign Takeoff Engine (STE): Observable-Only Supergrowth Laws for No-Meta Autonomous Intelligence",
        "doi": "https://doi.org/10.5281/zenodo.18828900",
    },
    {
        "id": "mte_2026",
        "tex_path": ROOT / "paper" / "Metrology-Theoretic Epistemics Engine.tex",
        "title": "Metrology-Theoretic Epistemics Engine (MTE): Observable-Only Metrology for Long-Horizon Autonomous Intelligence",
        "doi": "https://doi.org/10.5281/zenodo.18845340",
    },
]

REQUIRED_PATHS = [
    "AGENTS.md",
    "README.md",
    "CITATION.cff",
    "spec/glossary.md",
    "spec/ste_gate_spec.yaml",
    "spec/mte_epistemics_spec.yaml",
    "spec/metrics.yaml",
    "spec/log_format.yaml",
    "spec/repo_manifest.json",
    "spec/paper_alignment.yaml",
    "schemas/log_event.schema.json",
    "schemas/results.schema.json",
    "schemas/metrics.schema.json",
    "schemas/audit_report.schema.json",
    "ref_impl/ste_sim.py",
    "ref_impl/mte_core.py",
    "ref_impl/replay.py",
    "ref_impl/metrics.py",
    "bench/scenarios.yaml",
    "bench/generate_logs.py",
    "experiments/audit_repo.py",
    "experiments/reproduce.py",
    "cli/run.py",
]

TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".cff",
    ".txt",
    ".gitignore",
}
ABSOLUTE_PATH_PATTERN = re.compile(r"([A-Za-z]:\\\\Users\\\\|/Users/|/home/)")
STRONG_SECRET_PATTERNS = {
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "github_pat": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "openai_like_key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
}
WEAK_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)
REQUIRED_GITIGNORE_SECURITY_PATTERNS = [
    "results/*",
    "!results/.gitignore",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
]


def _sanitize_latex_title(raw: str) -> str:
    text = raw.replace("\\\\", " ")
    text = re.sub(r"\\[a-zA-Z]+\{", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_ste_title(tex: str) -> str:
    match = re.search(r"pdftitle=\{([^}]*)\}", tex, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return _sanitize_latex_title(match.group(1))
    match = re.search(r"\\title\{(.+?)\}", tex, flags=re.DOTALL)
    if match:
        return _sanitize_latex_title(match.group(1))
    return ""


def _extract_mte_title(tex: str) -> str:
    match = re.search(r"\\Title\{([^}]*)\}", tex, flags=re.DOTALL)
    if match:
        return _sanitize_latex_title(match.group(1))
    match = re.search(r"\\title\{(.+?)\}", tex, flags=re.DOTALL)
    if match:
        return _sanitize_latex_title(match.group(1))
    return ""


def _extract_titles_from_tex() -> Dict[str, str]:
    ste_text = EXPECTED_PAPERS[0]["tex_path"].read_text(encoding="utf-8", errors="ignore")
    mte_text = EXPECTED_PAPERS[1]["tex_path"].read_text(encoding="utf-8", errors="ignore")
    return {
        "ste_2026": _extract_ste_title(ste_text),
        "mte_2026": _extract_mte_title(mte_text),
    }


def _keyword_hits_in_snippet(readme_text: str, line_count: int = 10) -> Dict[str, bool]:
    snippet = "\n".join(readme_text.splitlines()[:line_count]).lower()
    return {keyword: (keyword.lower() in snippet) for keyword in SNIPPET_KEYWORDS}


def _presence_checks() -> Tuple[Dict[str, bool], List[str]]:
    status = {}
    missing: List[str] = []
    for rel_path in REQUIRED_PATHS:
        exists = (ROOT / rel_path).exists()
        status[rel_path] = exists
        if not exists:
            missing.append(rel_path)
    return status, missing


def _check_citation_and_readme(
    readme_text: str, citation: Dict[str, Any], extracted_titles: Dict[str, str]
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    failures: List[str] = []

    readme_lower = readme_text.lower()
    references = citation.get("references", [])
    citation_dois = {str(ref.get("doi", "")).strip().lower() for ref in references}
    citation_titles = {str(ref.get("title", "")).strip() for ref in references}

    paper_checks: List[Dict[str, Any]] = []
    for expected in EXPECTED_PAPERS:
        expected_doi = expected["doi"].lower()
        expected_title = expected["title"]
        tex_title = extracted_titles.get(expected["id"], "")

        doi_in_readme = expected_doi in readme_lower
        doi_in_citation = expected_doi.replace("https://doi.org/", "") in citation_dois
        title_in_citation = expected_title in citation_titles
        title_match_tex = tex_title == expected_title

        if not doi_in_readme:
            failures.append(f"README missing DOI: {expected['doi']}")
        if not doi_in_citation:
            failures.append(f"CITATION missing DOI: {expected['doi']}")
        if not title_in_citation:
            failures.append(f"CITATION missing title: {expected_title}")
        if not title_match_tex:
            failures.append(f"TeX title mismatch for {expected['id']}: '{tex_title}'")

        paper_checks.append(
            {
                "paper_id": expected["id"],
                "title_match_tex": title_match_tex,
                "doi_in_readme": doi_in_readme,
                "doi_in_citation": doi_in_citation,
                "title_in_citation": title_in_citation,
            }
        )

    if "minimal" not in readme_lower or "proxy" not in readme_lower:
        warnings.append("README should explicitly preserve minimal/proxy non-claim language.")

    return {"papers": paper_checks}, warnings, failures


def _check_alignment_map() -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    failures: List[str] = []

    alignment = read_yaml(ROOT / "spec" / "paper_alignment.yaml")
    mappings = alignment.get("concept_mapping", [])
    non_claims = alignment.get("non_claims", [])

    if len(mappings) < 6:
        failures.append("paper_alignment concept_mapping count must be >= 6.")
    if len(non_claims) < 3:
        warnings.append("paper_alignment should include at least 3 explicit non-claims.")
    warnings.append(
        "Strict theorem-level equivalence is not claimed; alignment is explicit proxy-level mapping."
    )

    missing_proxy_paths: List[str] = []
    for entry in mappings:
        proxy = str(entry.get("repo_proxy", ""))
        path_token = proxy.split()[0]
        if "/" in path_token and not (ROOT / path_token).exists():
            missing_proxy_paths.append(path_token)
    if missing_proxy_paths:
        failures.append(f"paper_alignment references missing files: {sorted(set(missing_proxy_paths))}")

    return {
        "mapping_count": len(mappings),
        "non_claim_count": len(non_claims),
        "missing_proxy_paths": sorted(set(missing_proxy_paths)),
        "strict_theorem_equivalence": False,
    }, warnings, failures


def _iter_text_files() -> List[Path]:
    files: List[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        rel = to_repo_relative(path)
        if rel.startswith("results/audit_report_"):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return files


def _check_security_surfaces() -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    failures: List[str] = []

    absolute_path_hits: List[Dict[str, str]] = []
    strong_secret_hits: List[Dict[str, str]] = []
    weak_secret_hits: List[Dict[str, str]] = []

    for path in _iter_text_files():
        rel_path = to_repo_relative(path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        abs_match = None if rel_path == "experiments/audit_repo.py" else ABSOLUTE_PATH_PATTERN.search(text)
        if abs_match:
            absolute_path_hits.append(
                {
                    "file": rel_path,
                    "sample": abs_match.group(0),
                }
            )

        weak_match = WEAK_SECRET_ASSIGNMENT_PATTERN.search(text)
        if weak_match:
            weak_secret_hits.append(
                {
                    "file": rel_path,
                    "pattern": weak_match.group(1).lower(),
                }
            )

        for pattern_name, pattern in STRONG_SECRET_PATTERNS.items():
            strong_match = pattern.search(text)
            if strong_match:
                strong_secret_hits.append(
                    {
                        "file": rel_path,
                        "pattern": pattern_name,
                    }
                )

    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="ignore")
    missing_gitignore_patterns = [
        pattern for pattern in REQUIRED_GITIGNORE_SECURITY_PATTERNS if pattern not in gitignore_text
    ]

    if strong_secret_hits:
        failures.append("Strong secret-like token(s) detected in repository files.")
    if absolute_path_hits:
        failures.append("Absolute local path literal(s) detected in repository files.")
    if missing_gitignore_patterns:
        warnings.append("Some recommended security ignore patterns are missing in .gitignore.")

    if weak_secret_hits:
        warnings.append("Weak secret-like assignments detected; verify these are placeholders only.")

    security_report = {
        "absolute_path_hits": absolute_path_hits,
        "strong_secret_hits": strong_secret_hits,
        "weak_secret_hits": weak_secret_hits,
        "missing_gitignore_patterns": missing_gitignore_patterns,
        "gitignore_security_patterns_complete": len(missing_gitignore_patterns) == 0,
    }
    return security_report, warnings, failures


def _run_reproducibility_checks(seed: int, scenario: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    failures: List[str] = []

    results_dir = ROOT / "results"
    first = run_reproduce(seed=seed, scenario=scenario, results_dir=results_dir)
    second = run_reproduce(seed=seed, scenario=scenario, results_dir=results_dir)
    validation = run_validate(seed=seed, scenario=scenario, results_dir=results_dir)
    benchmark = run_benchmark(seed=seed, results_dir=results_dir)

    same_hash = first["replay"]["primary_hash"] == second["replay"]["primary_hash"]
    same_payload = first["ste"] == second["ste"] and first["mte"] == second["mte"] and first["metrics"] == second["metrics"]

    if not validation["ok"]:
        failures.append("validate command reported errors.")
    if not same_hash or not same_payload:
        failures.append("repeat reproduce run is not deterministic.")

    plural = float(first["metrics"]["plural_feasibility"])
    if plural <= 0.0:
        warnings.append("plural_feasibility is zero; benchmark diversity signal is weak.")

    return (
        {
            "validate_ok": bool(validation["ok"]),
            "deterministic_hash": bool(same_hash),
            "deterministic_payload": bool(same_payload),
            "plural_feasibility": plural,
            "scenario_count": int(benchmark["scenario_count"]),
            "result_path": first["artifacts"]["result_path"],
        },
        warnings,
        failures,
    )


def run_repo_audit(seed: int = 0, scenario: str = "clean") -> Dict[str, Any]:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8", errors="ignore")
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8", errors="ignore")
    citation = read_yaml(ROOT / "CITATION.cff")

    presence_map, missing_required_paths = _presence_checks()
    keyword_hits = _keyword_hits_in_snippet(readme_text)
    extracted_titles = _extract_titles_from_tex()

    citation_report, citation_warnings, citation_failures = _check_citation_and_readme(
        readme_text=readme_text, citation=citation, extracted_titles=extracted_titles
    )
    alignment_report, alignment_warnings, alignment_failures = _check_alignment_map()
    reproducibility_report, reproducibility_warnings, reproducibility_failures = _run_reproducibility_checks(
        seed=seed, scenario=scenario
    )
    security_report, security_warnings, security_failures = _check_security_surfaces()

    agents_required_tokens = ["Purpose", "Inputs", "Outputs", "Primary Commands", "Extension Points"]
    agents_checks = {token: (token in agents_text) for token in agents_required_tokens}

    keyword_coverage = sum(int(v) for v in keyword_hits.values()) / float(len(keyword_hits))
    discoverability_score = int(round(100.0 * (0.6 * keyword_coverage + 0.2 * all(agents_checks.values()) + 0.2 * (len(missing_required_paths) == 0))))

    reproducibility_score = int(
        round(
            100.0
            * (
                0.4 * int(reproducibility_report["validate_ok"])
                + 0.3 * int(reproducibility_report["deterministic_hash"])
                + 0.2 * int(reproducibility_report["deterministic_payload"])
                + 0.1 * int(reproducibility_report["scenario_count"] >= 4)
            )
        )
    )

    paper_checks = citation_report["papers"]
    paper_alignment_score = int(
        round(
            100.0
            * (
                0.5 * (sum(int(item["title_match_tex"]) for item in paper_checks) / 2.0)
                + 0.3 * (sum(int(item["doi_in_citation"] and item["doi_in_readme"]) for item in paper_checks) / 2.0)
                + 0.2 * int(alignment_report["mapping_count"] >= 6)
            )
        )
    )
    security_score = int(
        round(
            100.0
            * (
                0.5 * int(len(security_report["strong_secret_hits"]) == 0)
                + 0.3 * int(len(security_report["absolute_path_hits"]) == 0)
                + 0.2 * int(security_report["gitignore_security_patterns_complete"])
            )
        )
    )
    security_score = max(0, security_score - min(20, 5 * len(security_report["weak_secret_hits"])))

    warnings: List[str] = []
    warnings.extend(citation_warnings)
    warnings.extend(alignment_warnings)
    warnings.extend(security_warnings)
    warnings.extend(reproducibility_warnings)

    hard_failures: List[str] = []
    if missing_required_paths:
        hard_failures.append(f"Missing required paths: {missing_required_paths}")
    hard_failures.extend(citation_failures)
    hard_failures.extend(alignment_failures)
    hard_failures.extend(security_failures)
    hard_failures.extend(reproducibility_failures)

    report: Dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": int(seed),
        "scenario": scenario,
        "status": "pass" if len(hard_failures) == 0 else "fail",
        "scores": {
            "discoverability": discoverability_score,
            "reproducibility": reproducibility_score,
            "paper_alignment": paper_alignment_score,
            "security": security_score,
            "overall": int(
                round(
                    (
                        discoverability_score
                        + reproducibility_score
                        + paper_alignment_score
                        + security_score
                    )
                    / 4.0
                )
            ),
        },
        "discoverability": {
            "required_paths_present": len(missing_required_paths) == 0,
            "missing_required_paths": missing_required_paths,
            "readme_snippet_keyword_hits": keyword_hits,
            "readme_snippet_keyword_coverage": keyword_coverage,
            "agents_sections": agents_checks,
        },
        "reproducibility": reproducibility_report,
        "paper_alignment": {
            "tex_extracted_titles": extracted_titles,
            "citation_checks": citation_report,
            "alignment_map": alignment_report,
        },
        "security": security_report,
        "warnings": warnings,
        "hard_failures": hard_failures,
    }

    schema_errors = validate_instance(report, load_schema("audit_report.schema.json"))
    if schema_errors:
        report["status"] = "fail"
        report["hard_failures"].append("audit_report_schema_validation_failed")
        report["hard_failures"].extend(schema_errors)

    out_dir = ensure_dir(ROOT / "results")
    out_path = out_dir / f"audit_report_seed{seed}.json"
    write_json(out_path, report)
    report["report_path"] = to_repo_relative(out_path)
    return report


def summarize_report(path: Path) -> Dict[str, Any]:
    payload = read_json(path)
    return {
        "status": payload["status"],
        "overall_score": payload["scores"]["overall"],
        "discoverability_score": payload["scores"]["discoverability"],
        "reproducibility_score": payload["scores"]["reproducibility"],
        "paper_alignment_score": payload["scores"]["paper_alignment"],
        "security_score": payload["scores"]["security"],
        "hard_failures": payload["hard_failures"],
        "warnings": payload["warnings"],
    }
