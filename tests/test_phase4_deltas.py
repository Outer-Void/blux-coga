from blux_coga.core.thinker import CogAThinker


def test_unclear_delta_is_structured():
    thinker = CogAThinker()
    _artifact, verdict = thinker.respond("idk")
    assert verdict.status.value == "UNCLEAR"
    assert verdict.delta is not None
    assert verdict.delta.minimal_change.startswith("clarification_needed:")


def test_contradiction_delta_is_structured():
    thinker = CogAThinker()
    thinker.respond("I want apples")
    _artifact, verdict = thinker.respond("I don't want apples")
    assert verdict.status.value == "UNCLEAR"
    assert verdict.delta is not None
    assert verdict.delta.minimal_change.startswith("clarification_needed:")
