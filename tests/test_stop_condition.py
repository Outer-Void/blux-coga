from blux_coga.core.thinker import CogAThinker


def test_stop_condition():
    thinker = CogAThinker()
    response = thinker.respond("stop")
    assert thinker.state.stopped is True
    assert "?" not in response.text
