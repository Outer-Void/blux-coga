## Determinism & Hashing

CogA normalizes each `ProblemSpec` before hashing. Normalization:

- Sorts dictionary keys recursively.
- Keeps array ordering stable while normalizing each element.

The normalized payload is serialized with stable JSON settings (sorted keys,
no extra whitespace) and hashed with SHA-256. The resulting `input_hash` is
included in every `run_header`, ensuring identical inputs produce byte-identical
outputs.

Implementation details live in:

- `src/blux_coga/contracts/determinism.py`
