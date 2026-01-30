from blux_coga.core.thinker import CogAThinker


def test_ambiguity_labeling():
    thinker = CogAThinker()
    response = thinker.respond("idk")
    assert "ambiguous/underspecified" in response.text
    assert "?" in response.text


def test_contradiction_detection():
    thinker = CogAThinker()
    thinker.respond("I want apples")
    response = thinker.respond("I don't want apples")
    lowered = response.text.lower()
    assert "potential contradiction noticed" in lowered
    assert "which one reflects what you mean right now?" in lowered


def test_summarize_command():
    thinker = CogAThinker()
    thinker.respond("I'm thinking about changing my routine.")
    thinker.respond("It feels hard to keep going.")
    response = thinker.respond("summarize")
    lowered = response.text.lower()
    assert "what i'm hearing is" in lowered
    for phrase in ("you should", "i recommend", "best approach", "next step"):
        assert phrase not in lowered


def test_freeze_command_exits():
    thinker = CogAThinker()
    response = thinker.respond("freeze")
    assert thinker.state.frozen is True
    assert "intent frozen" in response.text.lower()
    follow_up = thinker.respond("Anything else?")
    assert follow_up.text == ""
