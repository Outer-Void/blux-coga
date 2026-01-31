from blux_coga.core.boundaries import has_violation
from blux_coga.core.thinker import CogAThinker


def test_no_execution_language():
    thinker = CogAThinker()
    artifact, _verdict = thinker.respond("I feel stuck about my options.")
    texts = [
        artifact.response_text,
        artifact.reflection,
        *(artifact.clarifications),
        *(artifact.observations),
    ]
    assert not any(has_violation(text) for text in texts if text)
