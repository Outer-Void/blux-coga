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
    for option in artifact.options:
        texts.append(option.title)
        texts.extend(option.pros)
        texts.extend(option.cons)
        texts.extend(option.risks)
        texts.extend(option.unknowns)
    if artifact.comparison:
        texts.extend(artifact.comparison.criteria)
        for row in artifact.comparison.rows:
            texts.append(row.option_id)
            texts.extend(row.values)
    assert not any(has_violation(text) for text in texts if text)
