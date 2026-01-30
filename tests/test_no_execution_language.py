from blux_coga.core.thinker import CogAThinker


def test_no_execution_language():
    thinker = CogAThinker()
    response = thinker.respond("I feel stuck about my options.")
    lowered = response.text.lower()
    for phrase in ("you should", "the best approach", "i recommend", "next step"):
        assert phrase not in lowered
