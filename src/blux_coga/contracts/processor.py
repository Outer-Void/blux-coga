"""Contract processor for CogA reasoning artifacts."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from blux_coga.contracts.determinism import stable_hash
from blux_coga.contracts.models import (
    Check,
    Delta,
    ProblemSpec,
    ReasoningVerdict,
    RunHeader,
    ThoughtArtifact,
    VerdictStatus,
)
from blux_coga.core.boundaries import has_violation, enforce
from blux_coga.core.constants import CONTRACT_VERSION, MODEL_VERSION
from blux_coga.core.state import SessionState
from blux_coga.dialogue import engine
from blux_coga.dialogue.reflection import build_clarification, build_reflection


def _combine_response(
    reflection: str, observations: List[str], clarifications: List[str]
) -> str:
    pieces = [reflection] + observations + clarifications
    return "\n".join([piece for piece in pieces if piece])


def _base_flags(state: SessionState) -> Dict[str, bool]:
    return {
        "stop_signal": False,
        "freeze_signal": False,
        "summarize_signal": False,
        "short_or_vague": False,
        "ambiguous": False,
        "contradiction": False,
        "stopped_state": state.stopped,
        "frozen_state": state.frozen,
    }


def _artifact_from_state(
    run_header: RunHeader,
    user_input: str,
    state: SessionState,
) -> Tuple[ThoughtArtifact, VerdictStatus, Optional[str], Dict[str, bool]]:
    flags = _base_flags(state)
    reflection = ""
    clarifications: List[str] = []
    observations: List[str] = []
    contradiction_payload: Optional[Dict[str, str]] = None
    acknowledgment: Optional[str] = None
    summary: Optional[str] = None
    response_text = ""

    if state.frozen:
        artifact = ThoughtArtifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags

    if engine._is_freeze(user_input):
        flags["freeze_signal"] = True
        state.frozen = True
        state.stopped = True
        flags["stopped_state"] = True
        flags["frozen_state"] = True
        acknowledgment = "Intent frozen. I'll stop here."
        response_text = acknowledgment
        artifact = ThoughtArtifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags

    if engine._is_stop(user_input):
        flags["stop_signal"] = True
        state.stopped = True
        flags["stopped_state"] = True
        acknowledgment = "Acknowledged. I'll stop here."
        response_text = acknowledgment
        artifact = ThoughtArtifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags

    if engine._is_summarize(user_input):
        flags["summarize_signal"] = True
        summary = engine._summarize_intent(state)
        intent = state.extracted_intent or ""
        reflection = build_reflection(intent)
        clarifications = [build_clarification(intent)]
        fallback = _combine_response(reflection, [], clarifications)
        response_text = enforce(summary, fallback)
        artifact = ThoughtArtifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags

    contradiction = engine._detect_contradiction(
        user_input, state.last_user_utterances[:-1]
    )
    if contradiction:
        flags["contradiction"] = True
        earlier, later = contradiction
        contradiction_payload = {"earlier": earlier, "later": later}
        intent = engine._resolve_intent(user_input, state)
        reflection = build_reflection(intent)
        clarifications = [build_clarification(intent)]
        text = (
            "Potential contradiction noticed: "
            f"earlier you said \"{earlier}\", later you said \"{later}\".\n"
            "Which one reflects what you mean right now?"
        )
        fallback = _combine_response(reflection, [], clarifications)
        response_text = enforce(text, fallback)
        artifact = ThoughtArtifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return (
            artifact,
            VerdictStatus.UNCLEAR,
            "Clarify which statement reflects your current intent.",
            flags,
        )

    intent = engine._resolve_intent(user_input, state)
    reflection = build_reflection(intent)

    if engine._is_short_or_vague(user_input):
        flags["short_or_vague"] = True
        observations.append("This feels ambiguous/underspecified.")
        clarifications.append(build_clarification(intent))
    elif engine._detect_ambiguity(user_input):
        flags["ambiguous"] = True
        clarifications.append(build_clarification(intent))

    response_text = enforce(
        _combine_response(reflection, observations, clarifications),
        _combine_response(reflection, [], [build_clarification(intent)]),
    )

    artifact = ThoughtArtifact(
        run_header=run_header,
        reflection=reflection,
        clarifications=clarifications,
        observations=observations,
        flags=flags,
        contradiction=contradiction_payload,
        acknowledgment=acknowledgment,
        summary=summary,
        response_text=response_text,
    )

    if flags["short_or_vague"] or flags["ambiguous"]:
        return (
            artifact,
            VerdictStatus.UNCLEAR,
            "Share more specific detail about what you mean.",
            flags,
        )

    return artifact, VerdictStatus.COMPLETE, None, flags


def _check_non_directive(artifact: ThoughtArtifact) -> Check:
    texts = [
        artifact.reflection,
        artifact.response_text,
        artifact.acknowledgment or "",
        artifact.summary or "",
    ]
    texts.extend(artifact.clarifications)
    texts.extend(artifact.observations)
    if artifact.contradiction:
        texts.extend(list(artifact.contradiction.values()))
    violation = any(has_violation(text) for text in texts if text)
    status = "PASS" if not violation else "FAIL"
    message = "Non-directive language enforced."
    if violation:
        message = "Non-directive language violation detected."
    return Check(id="non_directive", status=status, message=message)


def _check_stop_state(flags: Dict[str, bool]) -> Check:
    message = "Stop signal received." if flags["stop_signal"] else "Stop not requested."
    return Check(id="stop_state", status="PASS", message=message)


def _check_freeze_state(flags: Dict[str, bool]) -> Check:
    message = (
        "Freeze signal received." if flags["freeze_signal"] else "Freeze not requested."
    )
    return Check(id="freeze_state", status="PASS", message=message)


def _check_ambiguity(flags: Dict[str, bool]) -> Check:
    flagged = flags["ambiguous"] or flags["short_or_vague"]
    status = "FLAG" if flagged else "PASS"
    message = "Ambiguity flagged." if flagged else "No ambiguity flagged."
    return Check(id="ambiguity", status=status, message=message)


def _check_contradiction(flags: Dict[str, bool]) -> Check:
    status = "FLAG" if flags["contradiction"] else "PASS"
    message = "Contradiction flagged." if flags["contradiction"] else "No contradiction."
    return Check(id="contradiction", status=status, message=message)


def run_contract(
    problem_spec: ProblemSpec,
) -> Tuple[ThoughtArtifact, ReasoningVerdict, SessionState]:
    run_header = RunHeader(
        input_hash=stable_hash(problem_spec),
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
    )
    state = problem_spec.to_session_state()
    user_input = problem_spec.user_input

    if state.frozen:
        artifact, status, delta_message, flags = _artifact_from_state(
            run_header, user_input, state
        )
        verdict = _build_verdict(run_header, status, delta_message, flags, artifact)
        return artifact, verdict, state

    state.add_turn("user", user_input)
    state.add_user_utterance(user_input)

    artifact, status, delta_message, flags = _artifact_from_state(
        run_header, user_input, state
    )

    state.add_turn("assistant", artifact.response_text)
    if not state.stopped and not state.frozen:
        state.last_intent = user_input
        state.extracted_intent = user_input

    verdict = _build_verdict(run_header, status, delta_message, flags, artifact)
    return artifact, verdict, state


def _build_verdict(
    run_header: RunHeader,
    status: VerdictStatus,
    delta_message: Optional[str],
    flags: Dict[str, bool],
    artifact: ThoughtArtifact,
) -> ReasoningVerdict:
    checks = [
        _check_non_directive(artifact),
        _check_stop_state(flags),
        _check_freeze_state(flags),
        _check_ambiguity(flags),
        _check_contradiction(flags),
    ]
    delta = None
    if status in (VerdictStatus.UNCLEAR, VerdictStatus.REFUSE):
        delta = Delta(minimal_change=delta_message or "Provide a minimal clarification.")
    return ReasoningVerdict(
        run_header=run_header,
        status=status,
        checks=checks,
        delta=delta,
    )
