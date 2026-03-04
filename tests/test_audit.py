from experiments.audit_repo import run_repo_audit


def test_repo_audit_passes_and_scores_are_bounded():
    report = run_repo_audit(seed=0, scenario="clean")
    assert report["status"] == "pass"
    assert report["hard_failures"] == []
    for key in ("discoverability", "reproducibility", "paper_alignment", "security", "overall"):
        assert 0 <= report["scores"][key] <= 100
    assert report["security"]["absolute_path_hits"] == []
    assert report["security"]["strong_secret_hits"] == []
