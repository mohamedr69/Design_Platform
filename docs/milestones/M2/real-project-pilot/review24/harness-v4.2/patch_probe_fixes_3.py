"""Recorded harness-v4 edit (review 22): the S7 probe reported the project's capacity at T0 from a counter read taken after
the resumed run (so the resume's own requests, stamped at T0 + 24 h + 1 s, fell inside the window and the figure read -2);
the capacity is now read immediately after the first run, before the resume. Reporting only; the runner's own recorded
deferral (needs 24, capacity 10) was and is the authoritative figure."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
p = HERE / "runner_probes.py"
s = p.read_text(encoding="utf-8")
o = 'd1 = run(root, ["r22dry-A", "L1", "L1"], env={"XTRACK_FAKE_NOW": str(T0)}, name="L1-T0")\nm1 = run_json(root, "L1")\n'
n = 'd1 = run(root, ["r22dry-A", "L1", "L1"], env={"XTRACK_FAKE_NOW": str(T0)}, name="L1-T0")\nm1 = run_json(root, "L1")\ncap_T0 = 60 - xtrack_used(root, "16830", T0)          # read BEFORE the resume: the resumed run\'s requests are stamped a day later\n'
assert s.count(o) == 1
s = s.replace(o, n)
o = '                                 "capacity_16830_at_T0": 60 - xtrack_used(root, "16830", T0)},'
n = '                                 "capacity_16830_at_T0": cap_T0},'
assert s.count(o) == 1
s = s.replace(o, n)
p.write_text(s, encoding="utf-8")
print("patched 3")
