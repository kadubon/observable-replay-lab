from ref_impl.metrics import (
    capture_sensitivity,
    evaluator_dependence,
    identifiability_margin,
    plural_feasibility,
    replay_consistency,
)


def test_metric_ranges_and_directionality():
    events = [
        {"observation": {"external_label": True}},
        {"observation": {"external_label": False}},
        {"observation": {"external_label": True}},
        {"observation": {"external_label": False}},
    ]

    assert evaluator_dependence(events) == 0.5
    assert 0.0 <= capture_sensitivity(10.0, 11.0) <= 1.0
    assert replay_consistency("abc", "abc") == 1.0
    assert replay_consistency("abc", "xyz") == 0.0
    assert plural_feasibility([True, False, True, True]) == 0.75

    strong_margin = identifiability_margin(True, 100.0)
    weak_margin = identifiability_margin(True, 1.0e9)
    assert 0.0 <= strong_margin <= 1.0
    assert 0.0 <= weak_margin <= 1.0
    assert strong_margin > weak_margin
