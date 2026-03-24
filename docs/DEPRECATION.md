## Deprecation policy

This repository exposes one frozen contract line: package `blux-coga` 1.0.0
with engine identity `CogA-1.0-pro`.

There are no active staged deprecations in this release because the freeze pass
removed non-canonical CLI aliases and alternate command paths instead of
carrying them forward behind a soft-deprecation promise.

The remaining support promise is the documented canonical CLI run command,
runner scripts that forward to it, and run-header backfill behavior documented
in `docs/COMPATIBILITY.md`.

Explicitly retired in this freeze line:

- top-level implicit run invocation
- short aliases `--in` and `--out`
- `accept` as a public CLI command
- any public interactive CLI contract
