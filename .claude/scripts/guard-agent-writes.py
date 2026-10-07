#!/usr/bin/env python3
"""PreToolUse guard for the read-only and evidence-only agents.

Claude Code cannot restrict Bash by verb in an agent's `tools` list, so this
hook reads the pending tool call from stdin and blocks (exit 2) anything that
would change the repository outside the folders the agent is allowed to write.

Usage in an agent's frontmatter:

    hooks:
      PreToolUse:
        - matcher: "Bash|Write|Edit|NotebookEdit"
          hooks:
            - type: command
              command: "python -I .claude/scripts/guard-agent-writes.py --allow docs/roadmap-evidence --allow docs/milestones"

Writes are always allowed under /tmp and any path containing "/scratchpad/".
Each --allow is a repository-relative folder (resolved against the hook's cwd)
the agent may also write to. With no --allow, the agent is read-only.

This is a safety net against accidental edits, not a sandbox: the orchestrator
still checks `git status` after every agent run.
"""
import json
import os
import re
import shlex
import sys

MUTATING_GIT = {
    "add", "am", "apply", "checkout", "cherry-pick", "clean", "commit", "fetch", "filter-branch",
    "gc", "merge", "mv", "notes", "pull", "push", "rebase", "reflog", "remote", "replace", "reset",
    "restore", "revert", "rm", "stash", "submodule", "switch", "update-index", "update-ref", "worktree",
}
WRITE_CMDS = {
    "rm", "rmdir", "mv", "cp", "tee", "truncate", "touch", "mkdir", "chmod", "chown", "ln", "dd",
    "install", "patch", "unlink", "shred", "rsync", "unzip", "tar", "git-lfs",
}
INPLACE_EDITORS = {"sed", "perl", "ruby"}
PY_WRITE_HINT = re.compile(r"open\([^)]*['\"][wa]|write_text|write_bytes|shutil\.|os\.remove|os\.unlink|os\.rename|os\.makedirs|Path\([^)]*\)\.(unlink|rename|mkdir)")
REDIRECT = re.compile(r"(?<![<>&0-9])[0-9]?>{1,2}\s*([^\s;&|]+)")


def allowed(path: str, roots: list[str], cwd: str) -> bool:
    if not path:
        return True
    p = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    if p.startswith("/tmp/") or "/scratchpad/" in p + "/":
        return True
    if p.startswith("/dev/") or p.startswith("/proc/"):
        return True
    return any(p == r or p.startswith(r + os.sep) for r in roots)


def block(reason: str) -> None:
    sys.stderr.write(f"guard-agent-writes: blocked. {reason}\n"
                     "This agent may not change the repository outside its allowed evidence folders; "
                     "put scratch files under the scratchpad and report the change for the orchestrator or implementer.\n")
    sys.exit(2)


def path_args(tokens: list[str]) -> list[str]:
    return [t for t in tokens if not t.startswith("-") and "=" not in t[:1]]


def check_bash(command: str, roots: list[str], cwd: str) -> None:
    for m in REDIRECT.finditer(command):
        target = m.group(1)
        if target.startswith("&"):
            continue
        if not allowed(target, roots, cwd):
            block(f"redirection writes to {target!r}.")
    for segment in re.split(r"\|\||&&|;|\||\n", command):
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            tokens = segment.split()
        # drop leading env assignments and wrappers
        while tokens and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]) or tokens[0] in ("sudo", "env", "nohup", "time", "command")):
            tokens.pop(0)
        if not tokens:
            continue
        cmd = os.path.basename(tokens[0])
        args = tokens[1:]
        if cmd == "git":
            sub = next((a for a in args if not a.startswith("-")), "")
            if sub in MUTATING_GIT:
                block(f"'git {sub}' changes the checkout or its history.")
            if sub == "branch" and any(a.startswith(("-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy")) for a in args):
                block("'git branch' with a delete/move/copy flag.")
            if sub == "tag" and any(a.startswith(("-d", "-a", "-s", "-f", "--delete")) for a in args) or (sub == "tag" and len([a for a in args if not a.startswith("-")]) > 1):
                block("'git tag' creating or deleting a tag.")
            continue
        if cmd in WRITE_CMDS:
            for p in path_args(args):
                if not allowed(p, roots, cwd):
                    block(f"'{cmd}' touches {p!r}.")
            continue
        if cmd in INPLACE_EDITORS and any(a.startswith("-i") or a == "--in-place" or re.match(r"^-[a-zA-Z]*i", a) for a in args):
            for p in path_args(args):
                if p not in ("-e",) and not allowed(p, roots, cwd):
                    block(f"'{cmd} -i' edits {p!r} in place.")
            continue
        if cmd in ("python", "python3", "py", "node"):
            inline = " ".join(args)
            if ("-c" in args or "-e" in args) and PY_WRITE_HINT.search(inline):
                block("inline script contains file-writing calls; write the script under the scratchpad and pass paths as arguments.")
            continue
        if cmd in ("npm", "npx", "pnpm", "yarn", "pip", "pip3", "uv") and any(a in ("uninstall", "remove", "rm", "prune") for a in args):
            continue  # package tooling never edits tracked files


def main() -> None:
    roots: list[str] = []
    argv = sys.argv[1:]
    while argv:
        a = argv.pop(0)
        if a == "--allow" and argv:
            roots.append(argv.pop(0))
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # malformed input: do not block
    cwd = payload.get("cwd") or os.getcwd()
    roots = [os.path.realpath(os.path.join(cwd, r)) for r in roots]
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if tool == "Bash":
        check_bash(tool_input.get("command") or "", roots, cwd)
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if not allowed(target, roots, cwd):
            block(f"{tool} to {target!r}.")
    sys.exit(0)


if __name__ == "__main__":
    main()
