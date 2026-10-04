# Exact commands and exit codes (four-arm readiness)

Interpreter `ep-platform/backend/venv/Scripts/python` (3.12); `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`; cwd `C:/t/iso/work/r2x/r26` unless stated. No provider or model request anywhere. The preflight ran with `PILOT_DRY=1` (scripted provider) in the new disposable root `C:/t/r2x/dry-runs/r26-preflight`.

| Step | Command | Exit | Result |
|---|---|---|---|
| Render the in-scope pages and text layers | `python render_r26.py` | 0 (second run, after fixing a long-path prefix) | 42 pages from the 26 PDFs; hashes in `renders/RENDERS.json` |
| Zoom crops for labelling | `python crop.py <Dnn> <page> x0 y0 x1 y1 [px] [rotate]` (repeated) | 0 | `label-evidence/crops/`, `CROPS.jsonl`. One early crop of a rotated page came out empty (a clip-coordinate bug in this helper, fixed); its log line was removed and it was re-cropped |
| Draft labels | per-document drafts `drafts/Dnn.json` (written by the assistant from the renders and crops) | — | 27 drafts |
| Assemble labels | `python labels_r26.py` | 0 | `labels-r26/` (register, page, uncertainty and exposure, evidence) |
| Parse check on the frozen evaluator | inline `m2_eval5.evaluate(...)` (cwd `C:/t/iso/frozen-r12/backend`, `AI_ENABLED=false`) | 0 | 27 documents, 31 expected components |
| Second pass and freeze | `python review_pass_r26.py` | 0 | `R26-REVIEW-PASS.json`; `LABEL-MANIFEST.r26.json` sha256 `b29d93d1…` |
| Final declaration | `python declare_final.py` | 0 | `FINAL-DECLARATION.json` sha256 `aec4d4df…` |
| Ledger enforcement demonstration | `python enforcement_r26.py` | 0 | 6 / 6 cases on a throw-away ledger |
| Scripted preflight of the exact binding | `bash preflight_r26.sh` (log `preflight/PREFLIGHT.log`) | every step 0 | the dry declaration; A; L1–L4; the v4 scorer |
| Preflight demand extraction | inline script, result `preflight/PREFLIGHT-DEMAND.json` | 0 | triggered pages and per-document requests |
| Bindings | `python bindings_r26.py` | 0 | `bindings/SOURCE-BINDINGS.json` |
| Package and check | `python package_r26.py`; `python verify_r26_package.py` | 0 / 0 | `evidence/PACKAGE-CHECK.json` `ok: true` |
| Response | `python append_response_r26.py 182e655607d5c084fb38e1c1da5ea47888b6f613ff7dbef1b4aa3c0793547374` | 0 | prefix byte-identical |

Not run: application or full test suites. The accepted Review 26 fresh tests (100 passed) are reused, because no harness or application file changed in this task.
