from blux_coga.core.thinker import CogAThinker


def test_conversation_continuity():
    thinker = CogAThinker()
    first = "I want to talk about how tired I feel lately."
    thinker.respond(first)
    response = thinker.respond("That has been hard.")
    assert "how tired I feel lately" in response.text
