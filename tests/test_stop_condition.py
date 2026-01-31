from blux_coga.core.thinker import CogAThinker


def test_stop_condition():
    thinker = CogAThinker()
    artifact, verdict = thinker.respond("stop")
    assert thinker.state.stopped is True
    assert "?" not in artifact.response_text
    assert verdict.status.value == "COMPLETE"
