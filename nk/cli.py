from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import task, workspace


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="nk")
    result.add_argument("command", nargs="?", choices=("init", "root", "task"))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments == ["--help"] or arguments == ["-h"]:
        parser().print_help(sys.stdout if arguments else sys.stderr)
        return 0 if arguments else 2
    command, rest = arguments[0], arguments[1:]
    if command == "task":
        return task.main(rest)
    if command in ("init", "root"):
        return workspace.main(arguments)
    parser().error(f"unknown command: {command}")
    return 2
