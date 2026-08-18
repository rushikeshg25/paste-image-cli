"""Command-line surface. Maps flags to output modes and exit codes."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__, core, store
from .backends import BackendError, NoBackendError, detect

EXIT_OK = 0
EXIT_NO_IMAGE = 1
EXIT_BACKEND_FAILED = 2
EXIT_NO_BACKEND = 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pasteimg",
        description="Save the clipboard image to a file and put its path on the clipboard, "
        "so you can paste it into a CLI agent (Claude Code, Codex).",
    )
    p.add_argument("--version", action="version", version=f"pasteimg {__version__}")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--print",
        dest="print_only",
        action="store_true",
        help="print the path only; leave the clipboard untouched",
    )
    mode.add_argument("--json", action="store_true", help="emit JSON for scripting")
    mode.add_argument(
        "--codex",
        action="store_true",
        help="save, then hand the image to `codex -i <path>`",
    )

    p.add_argument(
        "--last",
        action="store_true",
        help="re-emit the most recently saved image instead of reading the clipboard",
    )
    p.add_argument(
        "--prune-days",
        type=int,
        default=store.DEFAULT_PRUNE_DAYS,
        metavar="N",
        help=f"delete cached images older than N days (default {store.DEFAULT_PRUNE_DAYS}; 0 disables)",
    )
    p.add_argument(
        "--no-notify",
        action="store_true",
        help="suppress the desktop notification",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        result = _resolve(args)
    except core.NoImageError:
        print(
            "pasteimg: no image on the clipboard (copy a screenshot or image first)",
            file=sys.stderr,
        )
        return EXIT_NO_IMAGE
    except NoBackendError as exc:
        print(f"pasteimg: {exc}", file=sys.stderr)
        return EXIT_NO_BACKEND
    except BackendError as exc:
        print(f"pasteimg: {exc}", file=sys.stderr)
        return EXIT_BACKEND_FAILED

    return _emit(result, args)


def _resolve(args: argparse.Namespace) -> core.Grab:
    if args.last:
        path = store.latest()
        if path is None:
            raise core.NoImageError("no previously saved image")
        return core.Grab(path=path, size=path.stat().st_size, backend="cache", reused=True)
    return core.grab(prune_days=args.prune_days)


def _emit(result: core.Grab, args: argparse.Namespace) -> int:
    path = str(result.path)

    if args.json:
        print(json.dumps(result.as_dict()))
        return EXIT_OK

    if args.codex:
        # Replace this process with codex so it owns the terminal directly --
        # a TUI does not behave correctly as a subprocess.
        os.execvp("codex", ["codex", "-i", path])

    # --print and --last are read-only with respect to the clipboard: --print
    # is explicitly "don't touch it", and --last is a lookup, not a new paste.
    if not args.print_only and not args.last:
        clipboard = detect()
        clipboard.write_text(path)
        if not args.no_notify:
            clipboard.notify("Image path copied", f"{result.path.name} -- press Cmd+V")

    print(path)
    return EXIT_OK
