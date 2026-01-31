from blux_coga.core.thinker import CogAThinker


def test_options_and_comparison_for_or_input():
    thinker = CogAThinker()
    artifact, verdict = thinker.respond("I could stay or leave.")
    assert verdict.status.value == "UNCLEAR" or verdict.status.value == "COMPLETE"
    assert [option.id for option in artifact.options] == ["option-1", "option-2"]
    assert artifact.options[0].title.lower().startswith("i could stay")
    assert artifact.options[1].title.lower().startswith("leave")
    assert artifact.comparison is not None
    assert artifact.comparison.criteria == ["pros", "cons", "risks", "unknowns"]
    assert [row.option_id for row in artifact.comparison.rows] == [
        "option-1",
        "option-2",
    ]
    assert all(len(row.values) == 4 for row in artifact.comparison.rows)


def test_no_options_without_choice_language():
    thinker = CogAThinker()
    artifact, _verdict = thinker.respond("I'm thinking about a change.")
    assert artifact.options == []
    assert artifact.comparison is None
