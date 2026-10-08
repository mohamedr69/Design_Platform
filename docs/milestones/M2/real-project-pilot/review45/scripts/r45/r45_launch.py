"""R43-42 (review45, new): start ONE guarded process of this task with the cleaned environment (r45common.clean_env).
Usage: <bound python> -B r45_launch.py <guard dir> <roots ';'-separated> [--owner-hash-only] [--test-base] [--cwd DIR] -- <argv...>
The child (and every process it starts) loads the guard through PYTHONPATH; R43_GUARD_LOG is <work>/guard-log.
--owner-hash-only sets R43_GUARD_OWNER_RECORDS=hash-only (the snapshot alone); --test-base sets R45_GUARD_TEST_BASE=1 (the
harness test suite alone). The launcher itself writes nothing; it returns the child's exit code."""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402


def main(argv) -> int:
    i = argv.index("--")
    head, cmd = argv[:i], argv[i + 1:]
    guard, roots = head[0], head[1]
    extra = {}
    if "--owner-hash-only" in head:
        extra["R43_GUARD_OWNER_RECORDS"] = "hash-only"
    if "--test-base" in head:
        extra["R45_GUARD_TEST_BASE"] = "1"
    cwd = head[head.index("--cwd") + 1] if "--cwd" in head else None
    env = C.clean_env(guard, C.WORK / "guard-log", roots, extra)
    return subprocess.run(cmd, env=env, cwd=cwd).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
