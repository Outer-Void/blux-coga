# blux-coga — CogA, BLUX's structured reasoning engine

CogA turns an explicit, structured problem into an explicit, structured answer. A request lists the evidence
and the things to reason about: claims, tasks, options and criteria, items, risks. The artifact CogA returns
holds:

- the computed result;
- the evidence it rests on;
- a confidence value with its stated basis;
- the sources of uncertainty;
- findings about weak structure;
- links to dataset records;
- replay metadata.

Same request, same engine version: same bytes.

**CogA artifacts are BLUX-owned reasoning structures. They are not, and never contain, a model's hidden
chain-of-thought.** CogA 2 uses no model at all. Its seven algorithms are documented, deterministic
procedures over the fields you give it. Free text (claims, titles, questions) is carried through, never
interpreted, so it cannot change a result. Tests check this with prompt-injection inputs.

| capability | what it computes |
|---|---|
| `reason.analyze` | per-claim support/contradiction (noisy-OR of evidence reliability), dependency propagation, status |
| `reason.plan` | dependency order, stages, critical path, earliest/latest schedule, slack, parallel makespan |
| `reason.compare` | weighted multi-criteria scores, Pareto front, dominance, weight-sensitivity of the leader |
| `reason.decompose` | work tree, depth, leaves, work packages, acceptance coverage, untraced items |
| `reason.critique` | 13 exact structural rules (unsupported, circular, contradicted, single-source …) |
| `reason.rank` | ranking from scores, or Copeland ranking from pairwise preferences with cycle detection |
| `reason.risk` | inherent and residual likelihood x impact, mitigation effect, bands, appetite |

```bash
pip install -e '.[dev]'
coga compare request.json --pretty        # analyze | plan | compare | decompose | critique | rank | risk
coga replay artifact.json --request request.json
coga eval                                 # bundled regression + adversarial suite
coga schema compare [--artifact]          # the JSON Schemas (also in src/blux_coga/reason/schemas/)
```

Exit codes: `0` ok, `1` replay mismatch or failed evaluation, `2` usage, `3` invalid request.

## Documentation

| | |
|---|---|
| [docs/REASONING.md](docs/REASONING.md) | requests, artifacts, every algorithm, determinism, critique rules |
| [docs/USAGE.md](docs/USAGE.md) | the `coga` command line |
| [docs/EVALUATION.md](docs/EVALUATION.md) | regression and adversarial evaluation, dataset linkage |
| [docs/BLUX.md](docs/BLUX.md) | BLUX capabilities, receipts and replay through BLUX System |
| [docs/AUDIT-1.0.md](docs/AUDIT-1.0.md) | what CogA 1.0 was, and the dataset assumptions built on it |

## The frozen CogA 1.0 contract

`blux-coga run --input problem.json --output-dir out` still produces CogA 1.0's `thought_artifact.json` and
`reasoning_verdict.json` byte for byte, because
[blux-coga-dataset](https://github.com/Outer-Void/blux-coga-dataset) replays its fixtures against it. CI
runs that harness. That contract (`run_header.model_version: CogA-1.0-pro`) is a keyword-driven dialogue
processor, not a reasoning engine, and it is frozen. Its documents are `docs/CONTRACT.md`,
`docs/DETERMINISM.md`, `docs/BOUNDARIES.md`, `docs/REASONING_PACKS.md`, `docs/ACCEPTANCE.md`,
`docs/COMPATIBILITY.md`, `docs/DEPRECATION.md`, `docs/RUNBOOK.md`, `docs/PRO_NOTES.md` and
`docs/PLATFORMS.md`, and the runner scripts are `CogA*.sh`/`CogA.ps1`. New work uses `coga`.

## Development

```bash
make ci   # ruff + mypy --strict (CogA 2), generated files current, all tests, eval suite, clean-venv wheel
```

Python 3.10+, no runtime dependencies.

## Licence

BLUX Proprietary License, see [LICENSE](LICENSE).
