# Audit of CogA 1.0.0 (Stage 06)

Audited at `a7d88a2` (main; tag `CogA-0.1-mini`). All 32 tests passed, and `blux-coga-dataset`'s harness
replayed its fixtures cleanly.

## Architecture

- **Not a reasoning engine.** CogA 1.0 is a keyword-driven dialogue processor.
  - It recognizes `stop`, `freeze` and `summarize` as exact inputs.
  - It flags "ambiguity" by substrings (`maybe`, `kind of`, ` or `) and "vague" input by length (< 6
    characters).
  - It builds "options" by splitting the input on ` or `, and every option's `pros`, `cons`, `risks` and
    `unknowns` are empty. The comparison matrix is all empty strings.
  - It refuses only when the input contains both `override` and `boundary`, or both `bypass` and `safety`.
    That is evaded by rephrasing, and triggered by harmless text that uses those words.
- **Identity implies a model that is not there.** `run_header.model_version: CogA-1.0-pro` and the `cpu`/`gpu`
  profiles (`device`, `seed`, `max_steps`) suggest an inference model, but none exists. Profiles only change
  header fields.
- **The non-directive boundary is a phrase list** (`you should`, `i recommend`, sentences starting with
  `try`/`use`/…). Any other phrasing passes.
- **No evidence, confidence, uncertainty, dataset linkage or engine versioning** beyond header strings, and
  no BLUX adapter.
- **The runner scripts change the machine on every run.** `CogA.sh`, `CogA_mux.sh`, `CogA_proot.sh` and
  `CogA.ps1` create `.venv` and run `pip install -e .` (network) before each invocation.
- **Schemas are copied, not shared, and have already drifted.** `blux-coga-dataset/schemas/` has its own
  `thought_artifact` and `reasoning_verdict` schemas, and both now differ from CogA's.
- There was no CI.

## Dataset assumptions

`blux-coga-dataset` (`b3abf26`) records CogA 1.0's exact output for 10 fixtures and replays them through
`blux-coga run`. It assumes:

1. **The 1.0 contract never changes.** Kept: `blux-coga run` is frozen and byte-identical. CogA's CI now
   runs the dataset harness on every push.
2. **The engine is a model.** The metadata carries `model_version` and `device`, and the dataset card
   declares `task_categories: text-generation`. Nothing generates text: the outputs are template strings.
   This should be corrected in the dataset repository (an owner decision; not changed here).
3. **Coverage of the 1.0 behaviour is complete.** It is not. No fixture exercises the plain `stop` path.
   Changing that message (`Acknowledged. I'll stop here.`) passes the harness, while changing the `freeze`
   message fails it as it should.
4. **Records are the engine's reasoning.** They are dialogue templates. CogA 2's `reason.*` capabilities
   have no records in the dataset yet. Their regression and adversarial cases live in
   `src/blux_coga/reason/evals/` (dataset id `blux-coga-evals`).

## CogA 2.0

The seven `reason.*` capabilities are new, deterministic and documented (REASONING.md). The 1.0 code is left
untouched apart from the package version constant, which appears in no output.
