"""ORCH-06 (Review 33 C-6), agent R35EVAL-IMPL: can a DECLARED NORMALISER applied BEFORE evaluator .10 (without changing
the evaluator) reconcile it with the frozen harness literal_compare_r32 / lane_judge_r32, and would it be safe?

Usage (cwd inside C:/t/iso/work/r2x/r35; writes only <out json>):
  normaliser_experiment_r35.py --fixtures <SYNTHETIC-PREDICTIONS.json> --out <json> --normaliser N1|N2

This is an ANALYSIS of two hypothetical normalisers. Neither is proposed as bound code; nothing here changes the
evaluator, the candidate, the converter output or the harness. Same synthetic fixtures, same two channels, same evaluator
invocation as run_evaluator_offline_r32.py (whose functions are reused), register scope 'document' (shown equivalent to
'full' by the parity tests).

N1  blind (truth-independent), applied to every predicted value AND to the converter's truth encoding:
      identity  dash variants (literal_compare_r32.DASHES) -> '-' (non-Arabic only; .10 already ignores whitespace and case)
      revision  literal_compare_r32.norm_revision; 'R<n>' -> '<n>', anything else -> the whitespace-free string
      decision  an application word (approved / ANN / rejected) or a negative word stays; any other text -> the
                application's own evidence_reader.option_decision reading when it names one, else unchanged
N2  truth-aware (row-specific, uses the r32 truth), on top of N1:
      a predicted value that literal_compare_r32 matches to its own row is replaced by that row's (N1) evaluator encoding;
      an identity equal to ANOTHER page's identity of the same non-compilation document is dropped (the harness's
      cross-page copy: neither correct nor wrong); a decision that asserts no decision is dropped; the compilation
      files F002, F035, F043, F069 are split into one evaluator document per page (truth keyed by (pool id, page), (h)).
The harness verdicts are those of the frozen harness on the ORIGINAL pair (unchanged)."""
from __future__ import annotations

import argparse
import collections
import copy
import json
import os
import pathlib
import re
import sys
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402
import run_evaluator_offline_r32 as RUN  # noqa: E402

DROP = object()
COMPILATIONS = ("F002", "F035", "F043", "F069")


class Normaliser:
    def __init__(self, kind, LC, ER, truth, A):
        assert kind in ("N1", "N2"), kind
        self.kind, self.LC, self.ER, self.truth, self.A = kind, LC, ER, truth, A

    # --- N1 -------------------------------------------------------------------------------------------------------
    def n1(self, field, value):
        LC = self.LC
        if value is None:
            return None
        s = str(value)
        if field == "identity":
            return s if LC.is_arabic(s) else LC._DASH_RE.sub("-", s)
        if field == "revision":
            if LC.is_arabic(s):
                return s
            r = LC.norm_revision(s)
            m = re.fullmatch(r"R(\d+)", r)
            return m.group(1) if m else r
        low = s.strip().lower()
        if s in C.APPLICATION_DECISION_WORDS or low in LC.NEGATIVE_DECISION_WORDS:
            return s
        got = self.ER.option_decision(s)
        return got if got else s

    def n1_encoded(self, field, encoded):
        """The converter's truth encoding through N1 (negative and unscorable words unchanged)."""
        if encoded in (None, "absent", "ambiguous", "UR", "n/a"):
            return encoded
        return self.n1(field, encoded)

    def eval_input(self, REG, PAGE):
        fk = {"reference": "identity", "printed_revision": "revision", "decision": "decision"}
        R2, P2 = copy.deepcopy(REG), copy.deepcopy(PAGE)
        for d in R2["documents"]:
            for k, f in (("reference", "identity"), ("revision", "revision"), ("decision", "decision")):
                d["labels"][k] = self.n1_encoded(f, d["labels"].get(k))
        for pd in P2["documents"].values():
            for rec in pd["records"]:
                for k, f in fk.items():
                    rec[k] = self.n1_encoded(f, rec.get(k))
        if self.kind == "N2":
            R2, P2 = self.split_compilations(R2, P2)
        return R2, P2

    # --- N2 -------------------------------------------------------------------------------------------------------
    def split_compilations(self, REG, PAGE):
        regs, pages = [], {"documents": {}, "page1_corrections": PAGE.get("page1_corrections") or []}
        comp_keys = {self.truth["documents"][p]["doc_key"] for p in COMPILATIONS}
        for d in REG["documents"]:
            key = d["doc"]
            pd = PAGE["documents"][key]
            if key not in comp_keys:
                regs.append(d)
                pages["documents"][key] = pd
                continue
            all_pages = sorted({int(r["page"]) for r in pd["records"]} | {int(p) for p in pd["no_record_pages"]} |
                               {int(p) for p in pd["unvalidated_pages"]})
            for pg in all_pages:
                pk = f"{key}#p{pg}"
                regs.append({**d, "doc": pk})
                pages["documents"][pk] = {"records": [r for r in pd["records"] if int(r["page"]) == pg],
                                          "no_record_pages": {p: v for p, v in pd["no_record_pages"].items() if int(p) == pg},
                                          "unvalidated_pages": [p for p in pd["unvalidated_pages"] if int(p) == pg]}
        return {"documents": regs}, pages

    def doc_keys(self, pid, page=None):
        key = self.truth["documents"][pid]["doc_key"]
        if self.kind == "N2" and pid in COMPILATIONS:
            pages = sorted({int(r["page"]) for r in self.A.doc_rows(self.truth, pid)})
            return [f"{key}#p{page}"] if page is not None else [f"{key}#p{p}" for p in pages]
        return [key]

    def fact_value(self, pid, page, field, value):
        if value is None:
            return None
        if self.kind == "N1":
            return self.n1(field, value)
        LC = self.LC
        rec = self.truth["rows"][C.row_key(pid, page, field)]
        if rec["truth_kind"] == "value" and LC.compare_row(rec, value)["match"]:
            enc = {"identity": rec["literal"], "revision": rec["literal"],
                   "decision": {"approved": "approved", "approved as noted": "ANN", "revise and resubmit": "rejected",
                                "rejected": "rejected"}.get(rec.get("class"))}[field]
            return self.n1(field, enc)
        if field == "identity" and not self.truth["documents"][pid]["compilation"]:
            others = [o for o in self.A.doc_rows(self.truth, pid, "identity") if o["truth_kind"] == "value" and o["page"] != str(page)]
            if any(LC.compare_row(o, value)["match"] for o in others):
                return DROP
        if field == "decision" and not LC.asserts_decision(value):
            return DROP
        return self.n1(field, value)


def run(fixtures_path, out_path, kind):
    t0 = time.perf_counter()
    guard_info = RUN.install_guards()
    LC, J, A = C.import_harness()
    truth = C.load_json("truth_r32")
    ein = C.load_json("labels_eval_input")
    fx_all = json.loads(pathlib.Path(fixtures_path).read_text(encoding="utf-8"))
    assert fx_all["kind"] == "SYNTHETIC"
    EV, ER, TW, ev_info = RUN.load_evaluator()
    N = Normaliser(kind, LC, ER, truth, A)
    REG, PAGE = N.eval_input(ein["register"], ein["page"])
    ai_ctx = {"variant": "EV1", "profile": "default", "policies": [ER.EVIDENCE_POLICY_VERSION]}
    ctx_of = {"register": None, "ai_validated": ai_ctx}
    cases = []
    base_cache = {}
    for fx in fx_all["fixtures"]:
        pid, page, field, value = fx["pool_id"], fx["page"], fx["field"], fx["prediction"]["value"]
        doc = truth["documents"][pid]
        keys = N.doc_keys(pid)
        R_ = {"documents": [d for d in REG["documents"] if d["doc"] in keys]}
        P_ = {"documents": {k: PAGE["documents"][k] for k in keys}, "page1_corrections": PAGE.get("page1_corrections") or []}
        truth_rows = {(r["page"], r["field"]) for r in A.doc_rows(truth, pid)}

        def row_map(res):
            m = {}
            for k in keys:
                e = next(d for d in res["documents"] if d["doc"] == k)
                m.update(RUN.evaluator_row_map(e, PAGE["documents"][k]))
            return m

        if pid not in base_cache:
            base_cache[pid] = row_map(EV.evaluate(R_, P_, {}, [], ai_context=None))
            assert set(base_cache[pid]) == truth_rows, pid
        nv = N.fact_value(pid, page, field, value)
        for channel in ("register", "ai_validated"):
            ctx = ctx_of[channel]
            fkey = N.doc_keys(pid, page)[0]
            if nv is None or nv is DROP:
                rows = {}
            elif channel == "register":
                rows = {fkey: RUN.register_row(page, field, nv, doc["staged_sha256"])}
            else:
                rows = {fkey: RUN.ai_row(ER, page, field, nv, doc["staged_sha256"])}
            res = EV.evaluate(R_, P_, rows, [], ai_context=ctx)
            emap = row_map(res)
            assert set(emap) == truth_rows
            target = emap[(page, field)]
            h_pair = C.harness_judge(J, truth, pid, [] if value is None else
                                     [{"page": page, "field": field, "value": value, "state": RUN.POLICY_STATE[channel]}])
            hp = h_pair[(page, field)]
            side = []
            for rk in sorted(truth_rows, key=lambda x: (int(x[0]), C.FIELDS.index(x[1]))):
                if rk == (page, field):
                    continue
                if emap[rk]["verdict"] != h_pair[rk]["verdict"]:
                    tk = truth["rows"][C.row_key(pid, rk[0], rk[1])]["truth_kind"]
                    side.append({"row": C.row_key(pid, rk[0], rk[1]), "evaluator": emap[rk]["verdict"], "harness_pair": h_pair[rk]["verdict"],
                                 "class": RUN.classify(tk, emap[rk]["verdict"], h_pair[rk]["verdict"])})
            cases.append({"case_id": f"{fx['id']}/{channel}", "fixture_id": fx["id"], "channel": channel, "truth_key": fx["truth_key"],
                          "field": field, "truth_kind": fx["truth_kind"], "group": fx["group"], "variant": fx["variant"], "intent": fx["intent"],
                          "value": value, "normalised_value": "DROPPED" if nv is DROP else nv,
                          "application_reachable": RUN.application_reachable(field, value),
                          "evaluator_row_verdict": target["verdict"], "harness_pair": hp["verdict"],
                          "class_vs_pair": RUN.classify(fx["truth_kind"], target["verdict"], hp["verdict"]), "side_rows": side})
    out = {"kind": f"ORCH-06 normaliser experiment {kind} (analysis only; not bound code)", "statement": C.SYNTHETIC_STATEMENT,
           "normaliser": kind, "doc": __doc__, "fixtures_sha256": C.sha256_file(fixtures_path), "evaluator": ev_info,
           "guard": {"setup": guard_info, "blocked_calls": dict(RUN.GUARD["blocked"]), "violations": list(RUN.GUARD["violations"]),
                     "refused_writes": list(RUN.GUARD["refused_writes"])},
           "counts": {"class_vs_pair": dict(collections.Counter(c["class_vs_pair"] for c in cases)),
                      "class_vs_pair_reachable": dict(collections.Counter(c["class_vs_pair"] for c in cases if c["application_reachable"])),
                      "side_rows": dict(collections.Counter(s["class"] for c in cases for s in c["side_rows"]))},
           "cases": cases, "seconds": round(time.perf_counter() - t0, 1)}
    sha = C.write_json(out, pathlib.Path(out_path))
    return {"out": str(out_path), "sha256": sha, "counts": out["counts"], "seconds": out["seconds"], "guard": out["guard"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--normaliser", choices=("N1", "N2"), required=True)
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    assert out.is_absolute() and os.path.normcase(os.path.abspath(str(out))).startswith(RUN.WRITE_ALLOWED[0])
    assert os.path.normcase(os.getcwd()).startswith(RUN.WRITE_ALLOWED[0])
    s = run(pathlib.Path(a.fixtures), out, a.normaliser)
    print(json.dumps(s, indent=1, sort_keys=True, default=str))
    return 0 if not s["guard"]["violations"] and not s["guard"]["refused_writes"] else 1


if __name__ == "__main__":
    sys.exit(main())
