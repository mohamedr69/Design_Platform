"""converter_r32: round trip, reconciliation, and the frozen evaluator .10 truth reading of every converted row.
The candidate tree is imported READ-ONLY for its pure truth functions (no app import, no write: dont_write_bytecode).
Run: python -m pytest -q test_converter_r32.py"""
import importlib
import sys

import pytest

import converter_r32 as CV
import inputs_r32 as I
import labels_adapter_r32 as A

CAND_BACKEND = str(I.CANDIDATE / "backend")


@pytest.fixture(scope="module")
def truth():
    x = I.load_all()
    return A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])


@pytest.fixture(scope="module")
def out(truth):
    return CV.convert(truth)


@pytest.fixture(scope="module")
def ev4():
    sys.dont_write_bytecode = True
    sys.path.insert(0, CAND_BACKEND)
    try:
        mod = importlib.import_module("scripts.m2_eval4")
        assert mod.__file__.replace("\\", "/").startswith(CAND_BACKEND.replace("\\", "/"))
        yield mod
    finally:
        sys.path.remove(CAND_BACKEND)


def test_every_truth_row_maps_once_or_is_excluded(out, truth):
    t = CV.reconciliation_totals(out, truth)
    assert t["every_row_once"] and t["truth_rows"] == 432 and t["mapped"] + t["excluded"] == 432
    assert t["excluded"] == 15 and t["excluded_by_kind"] == {"value": 7, "absent": 8}, "F031 (4 pages) and F059 (1 page)"
    assert t["documents"] == 68 == t["planned"]


def test_round_trip_reproduces_kind_and_value(out, truth):
    back = CV.decode(out)
    for key, r in truth["rows"].items():
        if truth["documents"][r["pool_id"]]["is_alias"]:
            assert (r["pool_id"], r["page"], r["field"]) not in back
            continue
        kind, value = back[(r["pool_id"], r["page"], r["field"])]
        assert kind == r["truth_kind"], key
        if kind == "value":
            assert value == (CV.DECISION_WORD[r["class"]] if r["field"] == "decision" else r["literal"]), key
        if kind == "absent" and r["field"] == "decision":
            assert value == CV.ABSENT_DECISION[r["absent_kind"]], key


def test_compilations_are_page_keyed_records(out, truth):
    for pid in truth["compilations"]:
        key = truth["documents"][pid]["doc_key"]
        pd = out["page"]["documents"][key]
        pages = {r["page"] for r in pd["records"]} | {int(p) for p in pd["no_record_pages"]} | set(pd["unvalidated_pages"])
        assert pages == {int(p) for p in truth["documents"][pid]["labelled_pages"]}, pid
        assert len({r["component"] for r in pd["records"]}) == len(pd["records"])


def test_uncertainty_list_carries_every_not_scorable_row(out, truth):
    unc = {(u["pool_id"], str(u["page"]), u["field"]) for u in out["uncertainty"]["uncertainty"]}
    ns = {(r["pool_id"], r["page"], r["field"]) for r in truth["rows"].values() if r["truth_kind"] == "not_scorable" and not truth["documents"][r["pool_id"]]["is_alias"]}
    assert unc == ns and len(ns) == 32


def test_the_frozen_evaluator_reads_every_converted_row_as_the_r32_kind(out, truth, ev4):
    want = {"value": "readable", "absent": "negative", "not_scorable": "unscorable"}
    idx = out["r32_sidecar"]["pool_index"]
    seen = 0
    for key, pd in out["page"]["documents"].items():
        for rec in pd["records"]:
            for f in A.FIELDS:
                r = A.lookup(truth, idx[key], str(rec["page"]), f)
                if f == "identity":
                    state, _ = ev4.reference_truth(rec["reference"])
                elif f == "revision":
                    state, _ = ev4.revision_truth(rec["printed_revision"], rec["reference"])
                else:
                    state, _ = ev4.decision_truth(rec["decision"])
                assert state == want[r["truth_kind"]], (key, rec["page"], f, rec)
                seen += 1
    assert seen == 3 * sum(len(pd["records"]) for pd in out["page"]["documents"].values())


def test_sidecar_carries_what_evaluator_10_cannot_express(out):
    side = out["r32_sidecar"]
    assert len(side["decision_alternatives"]) == 7 and all(a["truth"] == "ANN" and a["also_correct"] == ["rejected"] for a in side["decision_alternatives"])
    assert any(a["alternates"] == ["B01-ASC-SD-ELE-0102-Rev.00"] for a in side["identity_alternates"])
    assert side["suffix_revision_divergences"] == []
    assert out["reference_set_statement"].endswith("not human-signed")


def test_planned_entries_bind_the_staged_hash(out, truth):
    for p in out["planned"]:
        d = truth["documents"][p["pool_id"]]
        assert p["sha256"] == d["staged_sha256"] and p["doc"] == d["doc_key"] and p["extension"] == ".pdf" and p["pages"] == d["page_count"]
