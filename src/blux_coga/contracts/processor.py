"""Contract processor for CogA reasoning artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import re

from blux_coga.contracts.determinism import stable_hash
from blux_coga.contracts.models import (
    Check,
    ComparisonMatrix,
    ComparisonRow,
    Delta,
    Option,
    ProblemSpec,
    Refusal,
    ReasoningVerdict,
    RunHeader,
    ThoughtArtifact,
    VerdictStatus,
)
from blux_coga.contracts.reasoning_packs import load_reasoning_pack
from blux_coga.core.boundaries import has_violation, enforce
from blux_coga.core.constants import (
    CONTRACT_VERSION,
    DEFAULT_REASONING_PACK_ID,
    MODEL_VERSION,
    SCHEMA_VERSION,
)
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
        "refuse_signal": False,
        "stopped_state": state.stopped,
        "frozen_state": state.frozen,
    }


def _artifact_from_state(
    run_header: RunHeader,
    user_input: str,
    state: SessionState,
) -> Tuple[
    ThoughtArtifact,
    VerdictStatus,
    Optional[str],
    Dict[str, bool],
    Optional[Refusal],
]:
    flags = _base_flags(state)
    reflection = ""
    clarifications: List[str] = []
    observations: List[str] = []
    contradiction_payload: Optional[Dict[str, str]] = None
    options: List[Option] = []
    comparison: Optional[ComparisonMatrix] = None
    acknowledgment: Optional[str] = None
    summary: Optional[str] = None
    response_text = ""
    refusal: Optional[Refusal] = None

    if state.frozen:
        options, comparison = _build_options_and_comparison(user_input)
        artifact = _make_artifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            options=options,
            comparison=comparison,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags, refusal

    if engine._is_freeze(user_input):
        flags["freeze_signal"] = True
        state.frozen = True
        state.stopped = True
        flags["stopped_state"] = True
        flags["frozen_state"] = True
        acknowledgment = "Intent frozen. I'll stop here."
        response_text = acknowledgment
        options, comparison = _build_options_and_comparison(user_input)
        artifact = _make_artifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            options=options,
            comparison=comparison,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags, refusal

    if engine._is_stop(user_input):
        flags["stop_signal"] = True
        state.stopped = True
        flags["stopped_state"] = True
        acknowledgment = "Acknowledged. I'll stop here."
        response_text = acknowledgment
        options, comparison = _build_options_and_comparison(user_input)
        artifact = _make_artifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            options=options,
            comparison=comparison,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags, refusal

    if engine._is_summarize(user_input):
        flags["summarize_signal"] = True
        summary = engine._summarize_intent(state)
        intent = state.extracted_intent or ""
        reflection = build_reflection(intent)
        clarifications = [build_clarification(intent)]
        fallback = _combine_response(reflection, [], clarifications)
        response_text = enforce(summary, fallback)
        options, comparison = _build_options_and_comparison(user_input)
        artifact = _make_artifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            options=options,
            comparison=comparison,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.COMPLETE, None, flags, refusal

    refusal_result = _should_refuse(user_input)
    if refusal_result:
        refusal, delta_message = refusal_result
        flags["refuse_signal"] = True
        response_text = "Unable to proceed with that request."
        options, comparison = _build_options_and_comparison(user_input)
        artifact = _make_artifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            options=options,
            comparison=comparison,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return artifact, VerdictStatus.REFUSE, delta_message, flags, refusal

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
        options, comparison = _build_options_and_comparison(user_input)
        artifact = _make_artifact(
            run_header=run_header,
            reflection=reflection,
            clarifications=clarifications,
            observations=observations,
            flags=flags,
            contradiction=contradiction_payload,
            options=options,
            comparison=comparison,
            acknowledgment=acknowledgment,
            summary=summary,
            response_text=response_text,
        )
        return (
            artifact,
            VerdictStatus.UNCLEAR,
            "clarification_needed: resolve_contradiction",
            flags,
            refusal,
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

    options, comparison = _build_options_and_comparison(user_input)
    artifact = _make_artifact(
        run_header=run_header,
        reflection=reflection,
        clarifications=clarifications,
        observations=observations,
        flags=flags,
        contradiction=contradiction_payload,
        options=options,
        comparison=comparison,
        acknowledgment=acknowledgment,
        summary=summary,
        response_text=response_text,
    )

    if flags["short_or_vague"] or flags["ambiguous"]:
        return (
            artifact,
            VerdictStatus.UNCLEAR,
            None,
            flags,
            refusal,
        )

    return artifact, VerdictStatus.COMPLETE, None, flags, refusal


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
    reasoning_pack = _load_reasoning_pack()
    run_header = RunHeader(
        input_hash=stable_hash(problem_spec),
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        reasoning_pack_id=reasoning_pack.pack_id,
        reasoning_pack_version=reasoning_pack.version,
        schema_version=SCHEMA_VERSION,
    )
    state = problem_spec.to_session_state()
    user_input = problem_spec.user_input

    if state.frozen:
        artifact, status, delta_message, flags, refusal = _artifact_from_state(
            run_header, user_input, state
        )
        verdict = _build_verdict(
            run_header, status, delta_message, flags, artifact, refusal
        )
        return artifact, verdict, state

    state.add_turn("user", user_input)
    state.add_user_utterance(user_input)

    artifact, status, delta_message, flags, refusal = _artifact_from_state(
        run_header, user_input, state
    )

    state.add_turn("assistant", artifact.response_text)
    if not state.stopped and not state.frozen:
        state.last_intent = user_input
        state.extracted_intent = user_input

    verdict = _build_verdict(
        run_header, status, delta_message, flags, artifact, refusal
    )
    return artifact, verdict, state


def _build_verdict(
    run_header: RunHeader,
    status: VerdictStatus,
    delta_message: Optional[str],
    flags: Dict[str, bool],
    artifact: ThoughtArtifact,
    refusal: Optional[Refusal],
) -> ReasoningVerdict:
    checks = [
        _check_non_directive(artifact),
        _check_stop_state(flags),
        _check_freeze_state(flags),
        _check_ambiguity(flags),
        _check_contradiction(flags),
    ]
    refusal_check = _check_refusal_reason(refusal)
    if refusal_check:
        checks.append(refusal_check)
    delta = None
    if status == VerdictStatus.UNCLEAR:
        delta = Delta(
            minimal_change=_sanitize_delta(
                delta_message
                or _select_unclear_delta(flags)
                or "clarification_needed: provide_minimal_context"
            )
        )
    if status == VerdictStatus.REFUSE and delta_message:
        delta = Delta(minimal_change=_sanitize_delta(delta_message))
    return ReasoningVerdict(
        run_header=run_header,
        status=status,
        checks=checks,
        delta=delta,
        refusal=refusal,
    )


def _sanitize_text(text: str, fallback: str) -> str:
    return enforce(text.strip(), fallback)


def _sanitize_list(items: List[str], keep_empty: bool = False) -> List[str]:
    sanitized = [_sanitize_text(item, "") for item in items]
    if keep_empty:
        return sanitized
    return [item for item in sanitized if item]


def _sanitize_optional(text: Optional[str], fallback: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    if has_violation(text):
        return fallback
    return text


def _sanitize_contradiction(
    payload: Optional[Dict[str, str]]
) -> Optional[Dict[str, str]]:
    if not payload:
        return None
    return {
        "earlier": _sanitize_text(payload.get("earlier", ""), "redacted statement"),
        "later": _sanitize_text(payload.get("later", ""), "redacted statement"),
    }


def _sanitize_delta(message: str) -> str:
    return _sanitize_text(message, "clarification_needed: provide_minimal_context")


def _make_artifact(
    run_header: RunHeader,
    reflection: str,
    clarifications: List[str],
    observations: List[str],
    flags: Dict[str, bool],
    contradiction: Optional[Dict[str, str]],
    options: List[Option],
    comparison: Optional[ComparisonMatrix],
    acknowledgment: Optional[str],
    summary: Optional[str],
    response_text: str,
) -> ThoughtArtifact:
    safe_reflection = _sanitize_text(reflection, "")
    safe_clarifications = _limit_list(
        _sanitize_list(clarifications), limit_key="clarifications"
    )
    safe_observations = _limit_list(
        _sanitize_list(observations), limit_key="observations"
    )
    safe_contradiction = _sanitize_contradiction(contradiction)
    safe_ack = _sanitize_optional(acknowledgment, None)
    safe_summary = _sanitize_optional(summary, None)
    safe_response = _sanitize_text(
        response_text,
        _combine_response(safe_reflection, safe_observations, safe_clarifications),
    )
    safe_options = _sanitize_options(options)
    safe_comparison = _sanitize_comparison(comparison)
    return ThoughtArtifact(
        run_header=run_header,
        reflection=safe_reflection,
        clarifications=safe_clarifications,
        observations=safe_observations,
        flags=flags,
        contradiction=safe_contradiction,
        options=safe_options,
        comparison=safe_comparison,
        acknowledgment=safe_ack,
        summary=safe_summary,
        response_text=safe_response,
    )


def _limit_list(items: List[str], limit_key: str) -> List[str]:
    from blux_coga.core.constants import MAX_CLARIFICATIONS, MAX_OBSERVATIONS

    if limit_key == "clarifications":
        limit = MAX_CLARIFICATIONS
    elif limit_key == "observations":
        limit = MAX_OBSERVATIONS
    else:
        limit = len(items)
    return items[:limit]


def _sanitize_options(options: List[Option]) -> List[Option]:
    sanitized: List[Option] = []
    for option in options:
        title = _sanitize_text(option.title, "Option")
        pros = _sanitize_list(option.pros)
        cons = _sanitize_list(option.cons)
        risks = _sanitize_list(option.risks)
        unknowns = _sanitize_list(option.unknowns)
        sanitized.append(
            Option(
                id=option.id,
                title=title,
                pros=pros,
                cons=cons,
                risks=risks,
                unknowns=unknowns,
            )
        )
    return sanitized


def _sanitize_comparison(
    comparison: Optional[ComparisonMatrix],
) -> Optional[ComparisonMatrix]:
    if not comparison:
        return None
    criteria = _sanitize_list(comparison.criteria)
    rows = [
        ComparisonRow(
            option_id=_sanitize_text(row.option_id, "option"),
            values=_sanitize_list(row.values, keep_empty=True),
        )
        for row in comparison.rows
    ]
    return ComparisonMatrix(criteria=criteria, rows=rows)


def _build_options_and_comparison(
    user_input: str,
) -> tuple[List[Option], Optional[ComparisonMatrix]]:
    titles = _extract_option_titles(user_input)
    if len(titles) < 2:
        return [], None
    titles = _limit_option_titles(titles)
    options: List[Option] = []
    for index, title in enumerate(titles, start=1):
        option_id = f"option-{index}"
        safe_title = _sanitize_text(title, f"Option {index}")
        options.append(
            Option(
                id=option_id,
                title=safe_title,
                pros=[],
                cons=[],
                risks=[],
                unknowns=[],
            )
        )
    criteria = ["pros", "cons", "risks", "unknowns"]
    rows = [
        ComparisonRow(option_id=option.id, values=["", "", "", ""])
        for option in options
    ]
    return options, ComparisonMatrix(criteria=criteria, rows=rows)


def _extract_option_titles(user_input: str) -> List[str]:
    pieces = re.split(r"\s+or\s+", user_input, flags=re.IGNORECASE)
    cleaned: List[str] = []
    seen = set()
    for piece in pieces:
        stripped = piece.strip(" .!?\"'")
        if stripped and stripped not in seen:
            cleaned.append(stripped)
            seen.add(stripped)
    return cleaned


def _limit_option_titles(titles: List[str]) -> List[str]:
    from blux_coga.core.constants import MAX_OPTIONS

    if len(titles) <= MAX_OPTIONS:
        return titles
    keyed = [
        (_normalize_option_title(title), index, title)
        for index, title in enumerate(titles)
    ]
    keyed.sort(key=lambda item: (item[0], item[1]))
    limited = [title for _norm, _idx, title in keyed[:MAX_OPTIONS]]
    return limited


def _normalize_option_title(title: str) -> str:
    return re.sub(r"[^\w\s]", "", title.lower()).strip()


def _select_unclear_delta(flags: Dict[str, bool]) -> Optional[str]:
    if flags.get("contradiction"):
        return "clarification_needed: resolve_contradiction"
    if flags.get("short_or_vague"):
        return "clarification_needed: add_specific_detail"
    if flags.get("ambiguous"):
        return "clarification_needed: disambiguate_request"
    return None


def _check_refusal_reason(refusal: Optional[Refusal]) -> Optional[Check]:
    if not refusal:
        return None
    return Check(
        id="refusal_reason",
        status="PASS",
        message="Refusal recorded.",
    )


def _should_refuse(user_input: str) -> Optional[tuple[Refusal, Optional[str]]]:
    lowered = user_input.lower()
    if "override" in lowered and "boundary" in lowered:
        return (
            Refusal(
                category="boundary_override",
                detail="request_conflicts_with_non_directive_boundary",
            ),
            None,
        )
    if "bypass" in lowered and "safety" in lowered:
        return (
            Refusal(
                category="safety_bypass",
                detail="request_conflicts_with_safety_constraints",
            ),
            None,
        )
    return None


def _load_reasoning_pack():
    packs_dir = Path(__file__).resolve().parents[3] / "reasoning_packs"
    return load_reasoning_pack(DEFAULT_REASONING_PACK_ID, packs_dir)
