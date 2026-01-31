from blux_coga.core.thinker import CogAThinker


def test_ambiguity_labeling():
    thinker = CogAThinker()
    artifact, verdict = thinker.respond("idk")
    assert "ambiguous/underspecified" in " ".join(artifact.observations).lower()
    assert "?" in artifact.response_text
    assert verdict.status.value == "UNCLEAR"


def test_contradiction_detection():
    thinker = CogAThinker()
    thinker.respond("I want apples")
    artifact, verdict = thinker.respond("I don't want apples")
    lowered = artifact.response_text.lower()
    assert "potential contradiction noticed" in lowered
    assert "which one reflects what you mean right now?" in lowered
    assert verdict.status.value == "UNCLEAR"


def test_summarize_command():
    thinker = CogAThinker()
    thinker.respond("I'm thinking about changing my routine.")
    thinker.respond("It feels hard to keep going.")
    artifact, _verdict = thinker.respond("summarize")
    lowered = artifact.response_text.lower()
    assert "what i'm hearing is" in lowered
    assert artifact.summary is not None


def test_freeze_command_exits():
    thinker = CogAThinker()
    artifact, verdict = thinker.respond("freeze")
    assert thinker.state.frozen is True
    assert "intent frozen" in artifact.response_text.lower()
    assert verdict.status.value == "COMPLETE"
    follow_up, _verdict = thinker.respond("Anything else?")
    assert follow_up.response_text == ""
