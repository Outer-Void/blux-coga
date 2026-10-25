# `coga` command line

| command | |
|---|---|
| `coga analyze\|plan\|compare\|decompose\|critique\|rank\|risk REQUEST [-o FILE] [--pretty]` | run a capability; `-` reads stdin |
| `coga replay ARTIFACT --request REQUEST [-o FILE]` | recompute; exit 1 unless input, artifact id and the whole document match. `-o` writes the recomputed artifact (linkage preserved) for `blux-system replay-check --output` |
| `coga validate CAP REQUEST` | schema and reference checks only |
| `coga schema CAP [--artifact]` | print the request (or artifact) JSON Schema |
| `coga eval [SUITE_DIR]` | run an evaluation suite (default: the bundled one); exit 1 if any case fails |
| `coga capabilities` | capability ids and algorithm versions |
| `coga --version` | engine and package versions |

`python -m blux_coga.reason` is the same command. `blux-coga run …` is the frozen CogA 1.0 contract (README).

Failures print `{"error": {"code", "message", "details"}}` on stdout and a one-line message on stderr, and
exit 3. Codes:

| code | meaning |
|---|---|
| `INVALID_REQUEST` | schema violation; the first error is in the message, up to 50 in `details.errors` |
| `DUPLICATE_ID` | two entries share an id |
| `UNKNOWN_REFERENCE` | a reference names nothing in the request |
| `DEPENDENCY_CYCLE` | a cycle where an order is required; the cycle is in `details.cycle` |
| `LIMIT_EXCEEDED` | a size limit was exceeded |
| `UNKNOWN_CAPABILITY` | no capability with that id |
| `INVALID_ARTIFACT` | `replay` was given something that is not a `coga.artifact` |
| `INVALID_SUITE` | `eval` could not read the suite |
| `UNREADABLE` | an input file could not be read |
