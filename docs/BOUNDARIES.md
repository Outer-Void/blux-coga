## Non-directive boundaries

CogA enforces a non-directive posture across all user-visible fields,
including:

- `ThoughtArtifact.response_text`
- `ThoughtArtifact.reflection`
- `ThoughtArtifact.clarifications[]`
- `ThoughtArtifact.observations[]`
- `ThoughtArtifact.acknowledgment`
- `ThoughtArtifact.summary`
- `ThoughtArtifact.contradiction.earlier`
- `ThoughtArtifact.contradiction.later`
- `ThoughtArtifact.options[].title`
- `ThoughtArtifact.options[].pros[]`
- `ThoughtArtifact.options[].cons[]`
- `ThoughtArtifact.options[].risks[]`
- `ThoughtArtifact.options[].unknowns[]`
- `ThoughtArtifact.comparison.criteria[]`
- `ThoughtArtifact.comparison.rows[].option_id`
- `ThoughtArtifact.comparison.rows[].values[]`
- `ReasoningVerdict.delta.minimal_change`
- `ReasoningVerdict.refusal.category`
- `ReasoningVerdict.refusal.detail`
- `ReasoningVerdict.checks[].message`

Blocked language includes directive or prescriptive phrasing such as:

- `you should`
- `i recommend`
- `best approach`
- `next step`
- `you need to`

When generated text would violate the boundary, CogA replaces it with a stable,
safer fallback rather than emitting prescriptive text.

`COMPLETE`, `UNCLEAR`, and `REFUSE` outputs all remain structured and subject to
this same boundary enforcement.

Implementation: `src/blux_coga/core/boundaries.py` and
`src/blux_coga/contracts/processor.py`.
