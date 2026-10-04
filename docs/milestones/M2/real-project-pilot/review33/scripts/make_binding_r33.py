"""ORCH-05.1: write BINDING-MANIFEST-R33.json (written once per freeze; a changed file is a new manifest, never an edit).
Usage: make_binding_r33.py <out path> [<run-set proposal path>]
Binds: every frozen input named by the task (inputs_r32.INPUTS with their recomputed sha256), the policy and its
amendment, the three package manifests, every harness-base and harness-r32 source and test, the run-set proposal, and
the candidate / baseline HEADs. The runner's preflight re-hashes every file under "files"."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

R33 = pathlib.Path("C:/t/iso/work/r2x/r33")
sys.path.insert(0, str(R33 / "harness-r32"))
import inputs_r32 as I  # noqa: E402


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main(out, run_set=None):
    files = {"inputs": {}, "harness_base": {}, "harness_r32": {}, "run_set": {}}
    for name, (path, expected) in sorted(I.INPUTS.items()):
        if pathlib.Path(path).is_dir():
            for f in sorted(pathlib.Path(path).glob("*.py")):
                files["inputs"][f.as_posix()] = sha(f)
            continue
        got = sha(path)
        if expected and got != expected:
            raise SystemExit(f"PACKET MISMATCH: {name} {got} != {expected}")
        files["inputs"][pathlib.Path(path).as_posix()] = got
    for f in sorted((R33 / "harness-base").glob("*.py")):
        files["harness_base"][f.as_posix()] = sha(f)
    for f in sorted((R33 / "harness-r32").glob("*.py")):
        files["harness_r32"][f.as_posix()] = sha(f)
    if run_set:
        files["run_set"][pathlib.Path(run_set).as_posix()] = sha(run_set)
    heads = {}
    for repo in ("C:/t/iso/cand-r29", "C:/t/iso/frozen-r12"):
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        heads[repo] = {"head": head, "clean": dirty == ""}
    man = {"name": "Review 33 correction (ORCH-05.1) binding manifest: r32 harness adapter, per-field scorer, C-4 concentration rule, run-set selector, guarded runner",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
           "candidate": {"tree": "C:/t/iso/cand-r29", "head": I.CANDIDATE_HEAD, "observed": heads["C:/t/iso/cand-r29"]},
           "baseline": {"tree": "C:/t/iso/frozen-r12", "head": I.BASELINE_HEAD, "observed": heads["C:/t/iso/frozen-r12"]},
           "policy_sha256": I.INPUTS["policy"][1], "policy_amendment_sha256": I.INPUTS["policy_amendment"][1],
           "reviewed2_labels_sha256": I.INPUTS["reviewed2_labels"][1], "reviewed2_package_manifest_sha256": I.INPUTS["reviewed2_manifest"][1],
           "packet_manifest_sha256": I.INPUTS["packet_manifest"][1], "review31_manifest_sha256": I.INPUTS["review31_manifest"][1],
           "review33_sha256": I.INPUTS["review33"][1],
           "reference_set_statement": I.REFERENCE_SET_STATEMENT, "files": files}
    if any(not v["clean"] or v["head"] != w for v, w in ((heads["C:/t/iso/cand-r29"], I.CANDIDATE_HEAD), (heads["C:/t/iso/frozen-r12"], I.BASELINE_HEAD))):
        raise SystemExit("PACKET MISMATCH: candidate or baseline HEAD / cleanliness")
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest(), sum(len(v) for v in files.values()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
