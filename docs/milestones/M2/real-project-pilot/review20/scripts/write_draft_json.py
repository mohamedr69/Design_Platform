"""Write pkg-src/EXPERIMENT-DRAFT.json: the structured DRAFT / NOT EXECUTED declaration (bound to the offline evidence
files by hash). No model request; nothing is executed."""
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x/review20")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
feas = json.loads((W / "feasibility/SAMPLE-FEASIBILITY.json").read_text(encoding="utf-8"))
work = json.loads((W / "workload/OBSERVED-WORKLOAD.json").read_text(encoding="utf-8"))
COMMON = {"guard": "G on", "support": "P3 = rotation-correct clip + local OCR fallback", "deadline": "D on (requires the D flag, section 9)",
          "variant": "EV1", "limits": {"per_document_profile": 12, "escalations": 2, "job_seconds": 120, "project_rolling_day": 60,
                                       "per_request_input_breaker_incl_cached": 70000}}
draft = {
    "status": "DRAFT / NOT EXECUTED / NOT AUTHORIZED TO RUN", "version": "isolated-accuracy-experiment-draft-2026-09-30.1",
    "requires_before_run": ["prerequisite implementation reviewed (D flag; coverage v3 scorer; optional decision-region strategy)",
                            "frozen, hashed final declaration binding every item of 'freeze'", "a separate owner budget decision"],
    "named_changes": {"G": "guard", "Rrot": "rotation-correct clipping", "Rocr": "local OCR fallback", "D": "deadline policy",
                      "ROI": "located title-block discovery", "X": "optional targeted context reads"},
    "live_arms": {"L1": {"discovery": "whole_page", "X": False, **COMMON}, "L2": {"discovery": "roi", "X": False, **COMMON},
                  "L3": {"discovery": "whole_page", "X": True, **COMMON}, "L4": {"discovery": "roi", "X": True, **COMMON},
                  "L1-D (optional)": {"discovery": "whole_page", "X": False, **{**COMMON, "deadline": "D off"}}},
    "contrasts": {"ROI alone": "L1->L2", "X on whole page": "L1->L3", "X on ROI": "L2->L4", "D alone (optional)": "L1-D->L1",
                  "G / Rrot / Rocr": "offline P0->P1->P2->P3 on each live arm's own captured responses (identical responses)",
                  "accepted reader vs L1": "COMBINED policy (G+Rrot+Rocr+D); never labelled rotation-only"},
    "offline_policies": {"P0": "guard off, accepted region text", "P1": "guard on, accepted region text", "P2": "guard on, rotation-correct clip only",
                         "P3": "guard on, rotation-correct clip + local OCR fallback"},
    "sample": {"pool": "415-document non-sealed exploration manifest minus every predicted / held-out document (sha256)",
               "pool_after_exclusion": feas["candidates"], "within_reader_scope_pdfs": sum(feas["strata_within_reader_scope"].values()),
               "strata_available": feas["strata_within_reader_scope"], "input_shapes": feas["input_shapes"],
               "proposed": {"rotated text-layer drawing sheets": 8, "rotation-0 text-layer drawing sheets": 4, "drawing-sheet scans": 3,
                            "A3/A4 text layer": 5, "A3/A4 scans": 4, "coverage controls": {"pdf_over_4_pages": 2, "word_file": 1}},
               "per_project_max": 3, "order": "sha256(seed | doc_key), new seed at freeze", "planned_denominator": 27},
    "labels": {"workflow": ["AI-drafted from source renders / text layer before any prediction, page / region bound",
                            "decision: present / absent, marked option, actor, legend, location vs title block (inside / outside / none)",
                            "independent owner-delegated AI source review of all decisions, all rotated / scanned items and a seeded 25 % subset",
                            "ambiguous -> unresolved (reported separately)", "no human signature implied or filled", "frozen with hashes"]},
    "coverage": "page / field-aware coverage v3 (draft prototype): every declared page, fail closed on missing pages, unsupported marked, transport separate",
    "gates": {"safety": "no critical false accept on a resolved label (stop rule); rule-of-three bound reported",
              "decision_coverage_for_ROI": "ROI arm decision coverage >= matching WP arm, counting off-title-block decisions; unknown is not coverage",
              "X": ">= 1 correctly associated fact per 8 extra requests at equal caps, no new false accept; CI including zero = no evidence of benefit",
              "deterministic_support": "offline on fresh responses; zero new wrong validations; OCR time bound reviewed",
              "coverage_honesty": "every planned page / file reported; timeouts charged at estimate"},
    "uncertainty": "Wilson 95 % intervals; per project and per layout; zero false accepts reported with the 3/n bound",
    "workload": {"observed": {"tasks": work["tasks"], "requests_per_planned_document": {k: v["requests_per_planned_document"] for k, v in work["arms"].items()}},
                 "proposed": {"L1": {"expected": 55, "cap": 65, "input_tokens": 850000}, "L2": {"expected": 52, "cap": 65, "input_tokens": 550000},
                              "L3": {"expected": 65, "cap": 75, "input_tokens": 950000}, "L4": {"expected": 62, "cap": 75, "input_tokens": 650000},
                              "L1-D (optional)": {"expected": 55, "cap": 65, "input_tokens": 850000}},
                 "total_core": {"expected_requests": 234, "declared_cap": 280, "input_tokens": 3000000, "output_tokens": 300000},
                 "total_with_optional": {"expected_requests": 289, "declared_cap": 345, "input_tokens": 3850000},
                 "price": "unknown: no dollar amount", "funding": "not from the original experiment's residual; a separate owner decision after review"},
    "evidence_files": {p: sha(W / p) for p in ("isolation/OFFLINE-ISOLATION-REPLAY.json", "feasibility/SAMPLE-FEASIBILITY.json",
                                               "coverage-v3/PILOT-COVERAGE-V3-DRAFT.json", "workload/OBSERVED-WORKLOAD.json",
                                               "coverage_v3_draft.py", "test_coverage_v3_draft.py")},
}
(W / "pkg-src/EXPERIMENT-DRAFT.json").write_text(json.dumps(draft, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("draft json written", sha(W / "pkg-src/EXPERIMENT-DRAFT.json")[:16])
