# blux-coga

BLUX-CogA is a conversational reasoning scaffold that focuses on non-directive
boundary enforcement. Responses avoid recommendations or execution language and
instead reflect back what the user shared while asking clarifying questions.

## Behavior overview

- **Non-directive boundary enforcement:** Output is filtered to avoid prescriptive
  language ("you should", "best approach", etc.).
- **Stop / freeze:** Entering `stop` halts the session; entering `freeze` halts and
  freezes intent state for the remainder of the session.
- **CLI harness:** A simple REPL is available via `blux-coga` for interactive use.
- **Tests exist:** Automated tests validate non-directive behavior and stop/freeze
  handling.
- **No execution, no recommendations:** The scaffold does not execute actions or
  recommend next steps.

## Usage

```bash
blux-coga
```

## Development

```bash
pytest
```
