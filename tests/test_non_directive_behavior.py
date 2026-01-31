from blux_coga.core.boundaries import has_violation
from blux_coga.core.thinker import CogAThinker


def test_non_directive_behavior():
    thinker = CogAThinker()
    artifact, verdict = thinker.respond("I'm deciding whether to change jobs.")
    texts = [
        artifact.response_text,
        artifact.reflection,
        *(artifact.clarifications),
        *(artifact.observations),
        artifact.acknowledgment or "",
        artifact.summary or "",
    ]
    assert any(check.id == "non_directive" for check in verdict.checks)
    assert not any(has_violation(text) for text in texts if text)
