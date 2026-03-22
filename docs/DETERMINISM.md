## Determinism

CogA normalizes each `ProblemSpec` before hashing:

- dictionaries are sorted recursively
- list ordering is preserved
- canonical JSON uses sorted keys and compact separators

The normalized payload is hashed with SHA-256 and emitted as `input_hash` in
both output `run_header` blocks.

Determinism in the frozen release covers:

- same `ProblemSpec` + same reasoning pack + same profile => byte-identical
  canonical JSON outputs
- canonical JSON serialization for artifacts and acceptance reports
- stable check ordering in `ReasoningVerdict`
- bounded clarification and observation counts
- deterministic selection of `UNCLEAR` deltas
- deterministic inclusion of profile metadata when a profile is used
- deterministic canonical filenames for file-mode and acceptance-harness runs

Implementation: `src/blux_coga/contracts/determinism.py`.
