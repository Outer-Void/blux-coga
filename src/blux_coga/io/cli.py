"""CLI harness for CogA."""

from __future__ import annotations

from blux_coga.core.thinker import CogAThinker


def main() -> None:
    thinker = CogAThinker()
    while True:
        try:
            user_input = input("> ")
        except EOFError:
            break
        response = thinker.respond(user_input)
        print(response.text)
        if thinker.state.stopped:
            break


if __name__ == "__main__":
    main()
