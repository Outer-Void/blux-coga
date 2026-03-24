## Determinism

CogA normalizes each `ProblemSpec` before hashing:

- dictionaries are sorted recursively
- list ordering is preserved
- canonical JSON uses sorted keys and compact separators

The normalized payload is hashed with SHA-256 and emitted as `input_hash` in
both output `run_header` blocks.

### Frozen deterministic guarantees

- same `ProblemSpec` + same reasoning pack + same profile => byte-identical
  canonical JSON outputs
- stable JSON serialization for artifacts, verdicts, and acceptance reports
- stable check ordering in `ReasoningVerdict`
- deterministic `UNCLEAR` delta selection
- deterministic inclusion of profile metadata only when a profile is selected
- canonical file-mode filenames:
  - `thought_artifact.json`
  - `reasoning_verdict.json`

### Determinism boundary

Determinism is defined for the canonical file-based interface and acceptance
harness. The internal stateful Python wrapper (`CogAThinker`) uses the same
deterministic processor, but it is not a canonical freeze integration surface.
External integrations should anchor to file mode output files.

### Export anchoring hashes

- `run_header.input_hash` is the canonical hash of normalized `ProblemSpec`
  input.
- A deterministic run artifact hash can be derived as SHA-256 over canonical
  `thought_artifact.json` bytes (or `reasoning_verdict.json` bytes) produced by
  stable serialization.

Implementation: `src/blux_coga/contracts/determinism.py` and
`src/blux_coga/contracts/processor.py`.
