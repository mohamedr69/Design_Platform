"""Recorded harness v4.2 edit after the first boundary-probe trial: an in-process failure entry now carries the journal
`seq` and the `pid` (as the journal-reconstructed entries do), so a provider stop whose three failures span a restart
(P5c) has uniform, journal-linked evidence. Additive; the streak logic is unchanged."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
p = HERE / "arm_ev.py"
s = p.read_text(encoding="utf-8")
o = '            state["recent_failures"].append({"sha256": kw.get("sha256"), **{k: entry.get(k) for k in ("task", "page", "outcome", "error_detail", "model")}})\n'
n = '            state["recent_failures"].append({"seq": jseq, "pid": os.getpid(), "sha256": kw.get("sha256"), **{k: entry.get(k) for k in ("task", "page", "outcome", "error_detail", "model")}})\n'
assert s.count(o) == 1
p.write_text(s.replace(o, n), encoding="utf-8")
print("patched provider recovery 2")
