## Non-directive Boundaries

CogA maintains a non-directive posture. It avoids prescriptive or execution
language and instead mirrors the user's intent while asking clarifying
questions. Boundary enforcement rejects directive phrases such as:

- "you should"
- "i recommend"
- "best approach"
- "next step"
- "you need to"

If candidate output violates boundary rules, CogA falls back to safer reflection
and clarification phrasing.

REFUSE behavior is used when a request explicitly conflicts with non-directive
or safety boundaries. Refusals include a structured category/detail pair and
avoid directive language in any artifact field.

Implementation details live in:

- `src/blux_coga/core/boundaries.py`
