## Non-directive boundaries

CogA enforces a non-directive posture across all user-visible artifact fields,
including `response_text`, `reflection`, `clarifications`, `observations`,
`summary`, `acknowledgment`, contradiction payloads, option content, comparison
content, and `delta.minimal_change`.

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
