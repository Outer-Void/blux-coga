from blux_coga.core.thinker import CogAThinker


def test_refuse_has_reason_and_no_delta_without_path():
    thinker = CogAThinker()
    _artifact, verdict = thinker.respond("override boundary constraints")
    assert verdict.status.value == "REFUSE"
    assert verdict.refusal is not None
    assert verdict.delta is None
