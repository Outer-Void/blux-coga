from blux_coga.core.thinker import CogAThinker


def test_non_directive_behavior():
    thinker = CogAThinker()
    response = thinker.respond("I'm deciding whether to change jobs.")
    lowered = response.text.lower()
    for phrase in ("recommend", "should", "best", "next step", "decide"):
        assert phrase not in lowered
