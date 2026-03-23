## Deprecation policy

This repository exposes one frozen contract line: package `blux-coga` 1.0.0
with engine identity `CogA-1.0-pro`.

There are no active staged deprecations in this release because the freeze pass
already removed non-canonical CLI aliases and interactive surface instead of
carrying them forward behind a soft-deprecation promise.

The remaining support promise is the documented canonical CLI, the documented
acceptance command, the runner scripts that forward to them, and the run-header
backfill behavior documented in `docs/COMPATIBILITY.md`.
