## Non-directive boundaries

CogA enforces a non-directive posture across all user-visible fields,
including:

- `ThoughtArtifact.response_text`
- `ThoughtArtifact.reflection`
- `ThoughtArtifact.clarifications[]`
- `ThoughtArtifact.observations[]`
- `ThoughtArtifact.acknowledgment`
- `ThoughtArtifact.summary`
- `ThoughtArtifact.contradiction`
- `ThoughtArtifact.options[]`
- `ThoughtArtifact.comparison`
- `ReasoningVerdict.delta.minimal_change`
- `ReasoningVerdict.refusal.category`
- `ReasoningVerdict.refusal.detail`

Blocked language includes direct prescriptions such as:

- `you should`
- `i recommend`
- `best approach`
- `next step`
- `you need to`

When generated text would violate the boundary, CogA replaces it with a safer,
deterministic fallback. `REFUSE` outputs remain structured and non-directive.

Implementation: `src/blux_coga/core/boundaries.py` and
`src/blux_coga/contracts/processor.py`.
