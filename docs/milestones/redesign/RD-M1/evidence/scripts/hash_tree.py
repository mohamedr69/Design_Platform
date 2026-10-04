"""Read-only hasher: SHA-256, size, mtime_ns for the audited trees.

Opens every file read-only; never writes beside a source. Output goes only to
the path given on the command line (inside the isolated scratch area).
"""
import hashlib
import json
import os
import subprocess
import sys
import time

EP = r"G:\dev (2)\dev\ep-platform"
OUTER = r"G:\dev (2)\dev"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def entry(p):
    st = os.stat(p)
    try:
        d = sha(p)
    except OSError as e:
        d = "ERROR:%s" % e
    return {"sha256": d, "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def git_files(repo):
    out = subprocess.run(["git", "-C", repo, "ls-files", "-co", "--exclude-standard", "-z"],
                         capture_output=True, check=True).stdout
    return [x.decode("utf-8") for x in out.split(b"\0") if x]


def walk(root):
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            yield os.path.join(dp, f)


def norm(p):
    return p.replace(os.sep, "/")


def main(out_path):
    result = {"taken_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "groups": {}}
    g = {}
    for rel in git_files(EP):
        p = os.path.join(EP, rel)
        if os.path.isfile(p):
            g[norm(rel)] = entry(p)
    result["groups"]["ep_platform_git_visible"] = g

    g = {}
    for sub in ("backend/uploads", "backend/app/redesign/library"):
        for p in walk(os.path.join(EP, sub)):
            g[norm(os.path.relpath(p, EP))] = entry(p)
    for rel in ("backend/.env", ".env"):
        p = os.path.join(EP, rel)
        if os.path.isfile(p):
            g[rel] = entry(p)
    # Live DB: metadata only (the main file legitimately changes on WAL checkpoints by the owner's services).
    for rel in ("backend/ep_platform.db", "backend/ep_platform.db-wal", "backend/ep_platform.db-shm"):
        p = os.path.join(EP, rel)
        if os.path.isfile(p):
            st = os.stat(p)
            g[rel] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "metadata_only": True}
    result["groups"]["ep_platform_ignored_relevant"] = g

    g = {}
    for rel in git_files(OUTER):
        if rel.startswith("ep-platform") or rel.startswith("<sibling clone folder>/"):
            continue
        p = os.path.join(OUTER, rel)
        if os.path.isfile(p):
            g[rel] = entry(p)
    result["groups"]["outer_repo_git_visible"] = g

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print({k: len(v) for k, v in result["groups"].items()})


if __name__ == "__main__":
    main(sys.argv[1])
