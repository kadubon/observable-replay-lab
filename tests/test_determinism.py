from bench.generate_logs import generate_scenario_events, load_scenarios
from ref_impl.replay import deterministic_replay


def test_same_input_same_output_hash():
    scenarios = load_scenarios()
    events = generate_scenario_events("clean", scenarios["clean"], seed=0)

    first_primary, first_replay, _ = deterministic_replay(events, seed=0)
    second_primary, second_replay, _ = deterministic_replay(events, seed=0)

    assert first_replay["match"] is True
    assert second_replay["match"] is True
    assert first_replay["primary_hash"] == second_replay["primary_hash"]
    assert first_primary == second_primary
