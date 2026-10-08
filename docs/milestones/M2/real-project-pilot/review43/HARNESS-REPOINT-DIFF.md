# Harness re-point diff: review42 -> review43 (task 38, R43-HARNESS-REPOINT)

Prepared by the ep-implementer (Claude Opus 5.5) on 2026-10-07. This prepares a v4 run; it authorizes nothing (no run, budget, scope, token, nonce or default).

## 1. What changed

- Copied: `review42/scripts/**` -> `review43/scripts/**`, 73 files, byte-identical before any edit (each review42 sha256 in `evidence/HARNESS-COPY-R42.json`).
- Changed: 20 files, 36 lines. Only the application-tree paths and their HEAD hashes were re-pointed; line endings preserved (byte-level replacement; CRLF files stay CRLF).
- Not changed: any gate, threshold, request limit, run set, truth, label, reference set, scoring rule, allowance, nonce or authorization logic; the sandbox base `C:/t/r2x/r42-sandbox`; the contract name `r42-live-contract-5`; the stamp `r32-v3`; every carried input hash.

Re-points (numbered):

| # | Old | New | Reason |
|---|---|---|---|
| 1 | `C:/t/iso/frozen-r12` | `C:/t/iso/frozen-r13` | baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| 1 | `c:/t/iso/frozen-r12` | `c:/t/iso/frozen-r13` | baseline application tree (case-folded form used by a child probe's assertion) |
| 2 | `C:/t/iso/cand-r29` | `C:/t/iso/cand-r30n` | candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| 2 | `c:/t/iso/cand-r29` | `c:/t/iso/cand-r30n` | candidate application tree (case-folded form used by a child probe's assertion) |
| 3 | `3d5607d99fcebf08ac45f5df937ad615ecc16fb3` | `7ec3d2cf983b70a604844beda8eb6b1ec6173d34` | baseline HEAD (full form) |
| 4 | `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` | `436daef215c72fbe2429dcd783e087bf39756ad7` | candidate HEAD (full form) |
| 3 | `3d5607d` | `7ec3d2c` | baseline HEAD (short form, docstring) |
| 4 | `a8aaced` | `436daef` | candidate HEAD (short form) |

## 2. Table (file, line, old, new, reason)

| File | Line | Old | New | Re-point and reason |
|---|---|---|---|---|
| `build/r42common.py` | 41 | `CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r29/backend")` | `CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r30n/backend")` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `build/r42common.py` | 42 | `BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")` | `BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r13/backend")` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| `build/r42common.py` | 43 | `CANDIDATE = ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d")` | `CANDIDATE = ("C:/t/iso/cand-r30n", "436daef215c72fbe2429dcd783e087bf39756ad7")` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2); #4 candidate HEAD (full form) |
| `build/r42common.py` | 44 | `BASELINE = ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")` | `BASELINE = ("C:/t/iso/frozen-r13", "7ec3d2cf983b70a604844beda8eb6b1ec6173d34")` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #3 baseline HEAD (full form) |
| `build/run_tests_r42.py` | 9 | `variables are removed. test_capture_store and test_run_control_r38 run from C:/t/iso/cand-r29/backend (read-only use).` | `variables are removed. test_capture_store and test_run_control_r38 run from C:/t/iso/cand-r30n/backend (read-only use).` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `build/run_tests_r42.py` | 95 | `f"--basetemp={basetemp / f'c{j:02d}'}"], cwd="C:/t/iso/cand-r29/backend",` | `f"--basetemp={basetemp / f'c{j:02d}'}"], cwd="C:/t/iso/cand-r30n/backend",` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/converter_r32.py` | 3 | `Format learned from C:/t/iso/cand-r29/backend/scripts/m2_eval6.py, m2_eval4.py and m2_pilot_eval.py (read-only, format only):` | `Format learned from C:/t/iso/cand-r30n/backend/scripts/m2_eval6.py, m2_eval4.py and m2_pilot_eval.py (read-only, format only):` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/drawings_ai_probe_r39.py` | 2 | `C:/t/iso/frozen-r12/backend or the candidate C:/t/iso/cand-r29/backend) by test_request_paths_r39.py, read-only use of the` | `C:/t/iso/frozen-r13/backend or the candidate C:/t/iso/cand-r30n/backend) by test_request_paths_r39.py, read-only use of the` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/drawings_ai_probe_r39.py` | 25 | `assert TREE.as_posix().lower() in ("c:/t/iso/frozen-r12/backend", "c:/t/iso/cand-r29/backend"), TREE` | `assert TREE.as_posix().lower() in ("c:/t/iso/frozen-r13/backend", "c:/t/iso/cand-r30n/backend"), TREE` | #1 baseline application tree (case-folded form used by a child probe's assertion); #2 candidate application tree (case-folded form used by a child probe's assertion) |
| `harness-r32/inputs_r32.py` | 20 | `CANDIDATE = pathlib.Path("C:/t/iso/cand-r29")` | `CANDIDATE = pathlib.Path("C:/t/iso/cand-r30n")` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/inputs_r32.py` | 21 | `BASELINE = pathlib.Path("C:/t/iso/frozen-r12")` | `BASELINE = pathlib.Path("C:/t/iso/frozen-r13")` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| `harness-r32/inputs_r32.py` | 22 | `CANDIDATE_HEAD = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"` | `CANDIDATE_HEAD = "436daef215c72fbe2429dcd783e087bf39756ad7"` | #4 candidate HEAD (full form) |
| `harness-r32/inputs_r32.py` | 23 | `BASELINE_HEAD = "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"` | `BASELINE_HEAD = "7ec3d2cf983b70a604844beda8eb6b1ec6173d34"` | #3 baseline HEAD (full form) |
| `harness-r32/lane_r32.py` | 3 | `B runs in the frozen baseline tree (cwd C:/t/iso/frozen-r12/backend), C, R and P in the candidate tree` | `B runs in the frozen baseline tree (cwd C:/t/iso/frozen-r13/backend), C, R and P in the candidate tree` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| `harness-r32/lane_r32.py` | 4 | `(cwd C:/t/iso/cand-r29/backend); every application root is the lane's sandbox (<sandbox base>/<stamp>/inv-<n>/<lane>).` | `(cwd C:/t/iso/cand-r30n/backend); every application root is the lane's sandbox (<sandbox base>/<stamp>/inv-<n>/<lane>).` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/preflight_r32.py` | 126 | `HEADS = {"C:/t/iso/frozen-r12": I.BASELINE_HEAD, "C:/t/iso/cand-r29": I.CANDIDATE_HEAD}` | `HEADS = {"C:/t/iso/frozen-r13": I.BASELINE_HEAD, "C:/t/iso/cand-r30n": I.CANDIDATE_HEAD}` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/project_bounds_r32.py` | 66 | `CANDIDATE = pathlib.Path("C:/t/iso/cand-r29/backend")` | `CANDIDATE = pathlib.Path("C:/t/iso/cand-r30n/backend")` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/project_bounds_r32.py` | 67 | `BASELINE = pathlib.Path("C:/t/iso/frozen-r12/backend")` | `BASELINE = pathlib.Path("C:/t/iso/frozen-r13/backend")` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| `harness-r32/request_paths_r39.py` | 23 | `TREES = {"baseline": pathlib.Path("C:/t/iso/frozen-r12/backend"), "candidate": pathlib.Path("C:/t/iso/cand-r29/backend")}` | `TREES = {"baseline": pathlib.Path("C:/t/iso/frozen-r13/backend"), "candidate": pathlib.Path("C:/t/iso/cand-r30n/backend")}` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/runner_r32.py` | 94 | `TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}` | `TREES = {"baseline": "C:/t/iso/frozen-r13/backend", "candidate": "C:/t/iso/cand-r30n/backend"}` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/sandbox_child_r32.py` | 1 | `"""ORCH-05.1 sandbox ingestion CHILD: runs inside the frozen baseline tree (C:/t/iso/frozen-r12/backend, B's code at` | `"""ORCH-05.1 sandbox ingestion CHILD: runs inside the frozen baseline tree (C:/t/iso/frozen-r13/backend, B's code at` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| `harness-r32/sandbox_child_r32.py` | 2 | `3d5607d) with every root pointed at the sandbox. It creates the schema (the application's own upgrade_to_head), the` | `7ec3d2c) with every root pointed at the sandbox. It creates the schema (the application's own upgrade_to_head), the` | #3 baseline HEAD (short form, docstring) |
| `harness-r32/sandbox_child_r32.py` | 24 | `assert TREE.as_posix().lower() == "c:/t/iso/frozen-r12/backend", TREE` | `assert TREE.as_posix().lower() == "c:/t/iso/frozen-r13/backend", TREE` | #1 baseline application tree (case-folded form used by a child probe's assertion) |
| `harness-r32/sandbox_ingest_r32.py` | 39 | `BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")` | `BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r13/backend")` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf) |
| `harness-r32/score_lane_r32.py` | 3 | `Usage (cwd C:/t/iso/cand-r29/backend, AI disabled, read-only use of the tree):` | `Usage (cwd C:/t/iso/cand-r30n/backend, AI disabled, read-only use of the tree):` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_capture_store.py` | 1 | `"""R31-04 capture-store contract, at the provider layer (no database, no model). Run from C:/t/iso/cand-r29/backend with` | `"""R31-04 capture-store contract, at the provider layer (no database, no model). Run from C:/t/iso/cand-r30n/backend with` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_portability_r42.py` | 136 | `assert PF.verify_isolation("C", ok, None, path_entries=[PF.ISOLATION_VENV + "/Lib/site-packages", "C:/t/iso/cand-r29/backend"], modules={})["ok"]` | `assert PF.verify_isolation("C", ok, None, path_entries=[PF.ISOLATION_VENV + "/Lib/site-packages", "C:/t/iso/cand-r30n/backend"], modules={})["ok"]` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_portability_r42.py` | 151 | `model_config = {"env_file": "C:/t/iso/cand-r29/backend/.env"}` | `model_config = {"env_file": "C:/t/iso/cand-r30n/backend/.env"}` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_portability_r42.py` | 166 | `for tree in ("C:/t/iso/frozen-r12/backend", "C:/t/iso/cand-r29/backend"):` | `for tree in ("C:/t/iso/frozen-r13/backend", "C:/t/iso/cand-r30n/backend"):` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_request_paths_r39.py` | 21 | `TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}` | `TREES = {"baseline": "C:/t/iso/frozen-r13/backend", "candidate": "C:/t/iso/cand-r30n/backend"}` | #1 baseline application tree: frozen-r12 -> frozen-r13 (R43 grammar remediation, HEAD 7ec3d2cf); #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_run_control_r38.py` | 4 | `and the probe's sample. Runs from C:/t/iso/cand-r29/backend (the capture store imports app.ai.provider; read-only use).` | `and the probe's sample. Runs from C:/t/iso/cand-r30n/backend (the capture store imports app.ai.provider; read-only use).` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/test_unread_pages_r39.py` | 27 | `r = subprocess.run([SI.PY, str(HERE / "unread_pages_probe_r39.py"), str(out)], cwd="C:/t/iso/cand-r29/backend", env=env, capture_output=True, text=True)` | `r = subprocess.run([SI.PY, str(HERE / "unread_pages_probe_r39.py"), str(out)], cwd="C:/t/iso/cand-r30n/backend", env=env, capture_output=True, text=True)` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/tripwire_r32.py` | 4 | `emission functions (scripts.m2_eval6 record_groups / observation_groups / ai_groups of C:/t/iso/cand-r29, imported` | `emission functions (scripts.m2_eval6 record_groups / observation_groups / ai_groups of C:/t/iso/cand-r30n, imported` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/tripwire_r32.py` | 23 | `CAND_BACKEND = "C:/t/iso/cand-r29/backend"` | `CAND_BACKEND = "C:/t/iso/cand-r30n/backend"` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/unread_pages_probe_r39.py` | 1 | `"""ORCH-08C (R39-06, task item 2): a CHILD process run inside the candidate tree (C:/t/iso/cand-r29/backend, read-only use)` | `"""ORCH-08C (R39-06, task item 2): a CHILD process run inside the candidate tree (C:/t/iso/cand-r30n/backend, read-only use)` | #2 candidate application tree: cand-r29 -> cand-r30n (the line-ending-normalized checkout of cand-r30, HEAD 436daef2) |
| `harness-r32/unread_pages_probe_r39.py` | 17 | `assert TREE.as_posix().lower() == "c:/t/iso/cand-r29/backend", TREE` | `assert TREE.as_posix().lower() == "c:/t/iso/cand-r30n/backend", TREE` | #2 candidate application tree (case-folded form used by a child probe's assertion) |

## 3. Files changed (sha256)

| File | review42 sha256 | review43 sha256 | Lines |
|---|---|---|---|
| `build/r42common.py` | `68f12396e9bb97a757412151db4498a0e062ee2ee346ee30357fc81aecc0a9b4` | `63bccd82ba45afd4aac06894687a63b59f9fd96241ca7fb6c7be1b1f31e66570` | 4 |
| `build/run_tests_r42.py` | `bed0672b578d329e953a3b531a8e1d809c30b8a0bd9b4cf4342042051c4b219d` | `68354157b207c5ac228459af0d80a0fe567743ef27db6ba5d11a0648ced6383d` | 2 |
| `harness-r32/converter_r32.py` | `4095a4967a7e7caa992feec4901e06c1836d263f62ab1ba884db8355c30f9704` | `ade5d0ea9a89216b700c61d0752375ff380b287d5ffb6b30fc6e321a2996a0ed` | 1 |
| `harness-r32/drawings_ai_probe_r39.py` | `510ac22b5498850dd7851ea674d35f821df96d2fd4b080e787e309aac5d8da93` | `d4d02aef32cd65633cbe4a6267077d4dbf70f50846bb3ee3d745fa9151d54656` | 2 |
| `harness-r32/inputs_r32.py` | `1bec5d3165a9921090ae5b5d93f1a94868b6aee700f8df50923796ff677379f5` | `7715a792deb8cc2e272ce69a9004fa45fef26193fc4a4d396869aa595240bb82` | 4 |
| `harness-r32/lane_r32.py` | `b6014a015a7b36b64cb0defc1b747681b4956770b1d9e4f8430d0dbb3fbcce68` | `d98790ca7c3583cd4b47b43dd9ff334409502f165014a03789b6814bdb25edaa` | 2 |
| `harness-r32/preflight_r32.py` | `8e652565b46e14dfdc2c7dfff0e4ec0e7aeec80b795e3f74b6d5a4f55c25174e` | `4b78972aa6656d8157faff870d4c706c22c4bb809ca7148dffd1138b6a740e88` | 1 |
| `harness-r32/project_bounds_r32.py` | `6abbf5eb04a72e55feb3883cb50730006f2caf1224c2e0edc63a23ef978c859b` | `e49b5a45f746d1331bf84c9395ebaa53563d6075bcf0d6ad11ea5d78c22b6427` | 2 |
| `harness-r32/request_paths_r39.py` | `0ee519859cca6921b57f082cd8b58b91cd429521a47ecf0f7066fd7a1950aee0` | `7f19cc82099de3e44f9eb913a686b9880699ad670c4b829025231fee20f1d089` | 1 |
| `harness-r32/runner_r32.py` | `53a20256747485d6dcd4744cb7106c7092590f4b41e5b73e959856178d282d55` | `87ca348e7912c7f7232ab39fb7c540c57adf3b886bbbe4f0af1b66f61bae1c9e` | 1 |
| `harness-r32/sandbox_child_r32.py` | `70684eb0a2b1a208dcf1e4e217bf039ed37cf4593b7fc1a0d63e21920cc27bba` | `8ed578abf38c7703927b3d3808bb17637bf0ce9e7308287fb466e665e748e9c1` | 3 |
| `harness-r32/sandbox_ingest_r32.py` | `73027343a1041500e40894c6f5615c4e18300659ca663c84a3a484859bfaaddc` | `55694b1ee32f3fe4289d44a731426e5cb2a1a62b5bd28f6e0c5d62fc03f38ad0` | 1 |
| `harness-r32/score_lane_r32.py` | `33a102d04bac562add88638008cd4561347225347115a3ad647b264a8a83832c` | `bf160fc048a980e9194cec0a72f2bb642e12321f65900a85a00b66bfea6d1043` | 1 |
| `harness-r32/test_capture_store.py` | `456f5a9e4a4aeb2946b009c9ca20229bc6344245a0539dacda9e9a855bf06936` | `577d4e1160182ddd2756b3f1642b9bb4b5e436f70e2e68af235f3a0bfe621660` | 1 |
| `harness-r32/test_portability_r42.py` | `965955eaa2e090d679a6e3c781e74bbbcf1961419016249f8c152400ea824d36` | `0cb9412b36c5dcf4793af639cc8929f05e7634a04ec7fefea7439acc34f510e8` | 3 |
| `harness-r32/test_request_paths_r39.py` | `ed1bc99df9f8b9bbdd02534602919b99d1c8a8d6eefb68dfe22de3c357707c76` | `067abe2f6b10b73cc0467e6ef81795435477e1c3385dcf3a5181ca54232f05f1` | 1 |
| `harness-r32/test_run_control_r38.py` | `43ef8d0e1571ed6665854b7dd79de55ca37e2e767fbf2a92941619b572e81768` | `997b6d6e8cd7bedc64218405a2fb38fe132f0ac4107c8bedb539ab2f8d9446f5` | 1 |
| `harness-r32/test_unread_pages_r39.py` | `329208bca4b4e03ccaf2eb0e9c5a28407e0b35bf31402fdfabe41e9489fb7604` | `53961f7c81f61da5142a784ab701638326751c900d2b0142e1a5527299dd82c5` | 1 |
| `harness-r32/tripwire_r32.py` | `2a67c268ac4ac641f59d6acca5867e1419670dd885a2340d4d64af60161ca389` | `2d3f6829bc1b9a0d6f56bf9bc77bbfeb35417a1a894e38e4e8df78a5882f6ec2` | 2 |
| `harness-r32/unread_pages_probe_r39.py` | `f326c362a0920e9c7f58d237d2cc41b4b5fc0525c5cb64f979f3c9166bbaf2cd` | `c071dc5b437a9f5a8f4a76191d2e1b5814dafeb50b626ba50abaf6c4890e7798` | 2 |

## 4. Other pins examined (not changed)

| Pin | Where (file:line) | Exact line | Invalidated by the R43 trees? | Action |
|---|---|---|---|---|
| parser-version string (parse-2026-09-28.6 vs the R43 parse-2026-10-07.10) | `harness-r32/*.py, build/*.py` | `(no occurrence of PARSER_VERSION or parse-20xx in any review42/review43 script)` | no: the harness does not pin the parser version | none |
| application source hashes used by the request bounds | `harness-r32/project_bounds_r32.py:68-81` | `"candidate/app/core/config.py": (CANDIDATE / "app/core/config.py", "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155"),` | no: the 10 pinned files are byte-equal in frozen-r13 and cand-r30n (the R43 change set does not touch them; cand-r30n bytes equal the blobs). On cand-r30 (CRLF on disk) they would differ | none (the reason cand-r30n exists) |
| review42 ledger state | `build/r42common.py:45` | `LEDGER_EXPECTED = {"entries": 483, "scopes": 17, "limit_amendments": 0}` | not by the R43 trees: by the v3 run (ledger now 484 / 18 / 0) | none; reported (build-script invariant only; the harness tests do not use it) |
| no authorization file anywhere under the sandbox base, r38 work folder and PILOT | `harness-r32/test_runner_r32.py:511-514` | `found = [str(p) for r in roots if r.exists() for p in r.rglob("OWNER-DISPATCH-AUTHORIZATION*.json")]` | not by the R43 trees: the owner's v3 authorization file declaration-r32-v3/OWNER-DISPATCH-AUTHORIZATION.json exists since the v3 run | none; the one failing test, reported not fixed |
| dry / test sandbox base | `harness-r32/preflight_r32.py:106; build/run_tests_r42.py:23` | `DEFAULT_SANDBOX_BASE = pathlib.Path("C:/t/r2x/r42-sandbox")` | no (not a tree pin; the basetemp must lie under it) | none |
| contract name, stamp and scope derived from r42 / v3 | `harness-r32/preflight_r32.py:105; build/r42common.py:27,30` | `CONTRACT = "r42-live-contract-5" / STAMP = "r32-v3" / SCOPE = f"m2-fresh-validation-r32-v3-{DECLARATION_DATE}"` | no for the trees; a v4 declaration will need its own stamp / scope (declaration work, not harness) | none |
| file-count assertion of the bound set | `(none in the harness; verify_binding counts whatever the manifest lists)` | `-` | no | none |
| R42 audit guard roots and log | `build/guard/sitecustomize.py:14-20,23` | `_ROOTS = ["c:/t/iso/work/r2x/r42", ..., "review42", "declaration-r32-v3", "<R42 session scratchpad>"]` | no for the trees; it names the R42 task's folders | package copy unchanged; the scratch run copy substituted (S1, S2 in evidence/RUN-COPY-SUBSTITUTIONS.json) |

## 5. Unified diff against review42

### `build/r42common.py`

```diff
--- review42/scripts/build/r42common.py
+++ review43/scripts/build/r42common.py
@@ -40,6 +40,6 @@
 
-CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r29/backend")
-BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")
-CANDIDATE = ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d")
-BASELINE = ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")
+CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r30n/backend")
+BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r13/backend")
+CANDIDATE = ("C:/t/iso/cand-r30n", "436daef215c72fbe2429dcd783e087bf39756ad7")
+BASELINE = ("C:/t/iso/frozen-r13", "7ec3d2cf983b70a604844beda8eb6b1ec6173d34")
 LEDGER_EXPECTED = {"entries": 483, "scopes": 17, "limit_amendments": 0}
```

### `build/run_tests_r42.py`

```diff
--- review42/scripts/build/run_tests_r42.py
+++ review43/scripts/build/run_tests_r42.py
@@ -8,3 +8,3 @@
 logged; TEMP / TMP point into the basetemp; AI_* / ANTHROPIC* / OPENAI* / CLAUDE* / owner-token / R38_SANDBOX_BASE
-variables are removed. test_capture_store and test_run_control_r38 run from C:/t/iso/cand-r29/backend (read-only use).
+variables are removed. test_capture_store and test_run_control_r38 run from C:/t/iso/cand-r30n/backend (read-only use).
 No model request; the AI ledger is opened mode=ro only."""
@@ -94,3 +94,3 @@
         r = subprocess.run([PY, "-B", "-m", "pytest", "-q", str(H / f"{m}.py"), f"--junitxml={x}", "--rootdir", str(H),
-                            f"--basetemp={basetemp / f'c{j:02d}'}"], cwd="C:/t/iso/cand-r29/backend",
+                            f"--basetemp={basetemp / f'c{j:02d}'}"], cwd="C:/t/iso/cand-r30n/backend",
                            env={**env, "PYTHONPATH": f"{H};{GUARD}", "AI_ENABLED": "false"}, capture_output=True, text=True)
```

### `harness-r32/converter_r32.py`

```diff
--- review42/scripts/harness-r32/converter_r32.py
+++ review43/scripts/harness-r32/converter_r32.py
@@ -2,3 +2,3 @@
 
-Format learned from C:/t/iso/cand-r29/backend/scripts/m2_eval6.py, m2_eval4.py and m2_pilot_eval.py (read-only, format only):
+Format learned from C:/t/iso/cand-r30n/backend/scripts/m2_eval6.py, m2_eval4.py and m2_pilot_eval.py (read-only, format only):
   register  {"documents": [{"doc": "EP-<ep>/<relative_path>", "ep", "labels": {"reference", "revision", "decision", "kind",
```

### `harness-r32/drawings_ai_probe_r39.py`

```diff
--- review42/scripts/harness-r32/drawings_ai_probe_r39.py
+++ review43/scripts/harness-r32/drawings_ai_probe_r39.py
@@ -1,3 +1,3 @@
 """ORCH-08C (R39-04, task item 1(b) and 1(d)): a CHILD process run inside one application tree (the frozen baseline
-C:/t/iso/frozen-r12/backend or the candidate C:/t/iso/cand-r29/backend) by test_request_paths_r39.py, read-only use of the
+C:/t/iso/frozen-r13/backend or the candidate C:/t/iso/cand-r30n/backend) by test_request_paths_r39.py, read-only use of the
 tree, every root in a sandbox under C:/t/r2x/r<NN>-sandbox/, no model and no network: the provider is a local fake.
@@ -24,3 +24,3 @@
 TREE = pathlib.Path(os.getcwd())
-assert TREE.as_posix().lower() in ("c:/t/iso/frozen-r12/backend", "c:/t/iso/cand-r29/backend"), TREE
+assert TREE.as_posix().lower() in ("c:/t/iso/frozen-r13/backend", "c:/t/iso/cand-r30n/backend"), TREE
 url = os.environ.get("DATABASE_URL", "")
```

### `harness-r32/inputs_r32.py`

```diff
--- review42/scripts/harness-r32/inputs_r32.py
+++ review43/scripts/harness-r32/inputs_r32.py
@@ -19,6 +19,6 @@
 AI_LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
-CANDIDATE = pathlib.Path("C:/t/iso/cand-r29")
-BASELINE = pathlib.Path("C:/t/iso/frozen-r12")
-CANDIDATE_HEAD = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"
-BASELINE_HEAD = "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
+CANDIDATE = pathlib.Path("C:/t/iso/cand-r30n")
+BASELINE = pathlib.Path("C:/t/iso/frozen-r13")
+CANDIDATE_HEAD = "436daef215c72fbe2429dcd783e087bf39756ad7"
+BASELINE_HEAD = "7ec3d2cf983b70a604844beda8eb6b1ec6173d34"
```

### `harness-r32/lane_r32.py`

```diff
--- review42/scripts/harness-r32/lane_r32.py
+++ review43/scripts/harness-r32/lane_r32.py
@@ -2,4 +2,4 @@
   lane_r32.py <B|C|R|P> <run config json abs>
-B runs in the frozen baseline tree (cwd C:/t/iso/frozen-r12/backend), C, R and P in the candidate tree
-(cwd C:/t/iso/cand-r29/backend); every application root is the lane's sandbox (<sandbox base>/<stamp>/inv-<n>/<lane>).
+B runs in the frozen baseline tree (cwd C:/t/iso/frozen-r13/backend), C, R and P in the candidate tree
+(cwd C:/t/iso/cand-r30n/backend); every application root is the lane's sandbox (<sandbox base>/<stamp>/inv-<n>/<lane>).
```

### `harness-r32/preflight_r32.py`

```diff
--- review42/scripts/harness-r32/preflight_r32.py
+++ review43/scripts/harness-r32/preflight_r32.py
@@ -125,3 +125,3 @@
 _SANDBOX_BASE_RE = re.compile(r"C:/t/r2x/r\d{2}-sandbox")
-HEADS = {"C:/t/iso/frozen-r12": I.BASELINE_HEAD, "C:/t/iso/cand-r29": I.CANDIDATE_HEAD}
+HEADS = {"C:/t/iso/frozen-r13": I.BASELINE_HEAD, "C:/t/iso/cand-r30n": I.CANDIDATE_HEAD}
 PLAN_CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
```

### `harness-r32/project_bounds_r32.py`

```diff
--- review42/scripts/harness-r32/project_bounds_r32.py
+++ review43/scripts/harness-r32/project_bounds_r32.py
@@ -65,4 +65,4 @@
 
-CANDIDATE = pathlib.Path("C:/t/iso/cand-r29/backend")
-BASELINE = pathlib.Path("C:/t/iso/frozen-r12/backend")
+CANDIDATE = pathlib.Path("C:/t/iso/cand-r30n/backend")
+BASELINE = pathlib.Path("C:/t/iso/frozen-r13/backend")
 SOURCES = {
```

### `harness-r32/request_paths_r39.py`

```diff
--- review42/scripts/harness-r32/request_paths_r39.py
+++ review43/scripts/harness-r32/request_paths_r39.py
@@ -22,3 +22,3 @@
 
-TREES = {"baseline": pathlib.Path("C:/t/iso/frozen-r12/backend"), "candidate": pathlib.Path("C:/t/iso/cand-r29/backend")}
+TREES = {"baseline": pathlib.Path("C:/t/iso/frozen-r13/backend"), "candidate": pathlib.Path("C:/t/iso/cand-r30n/backend")}
 ENTRIES = {"B": ("baseline", ["app.services.document_processing:run"]),
```

### `harness-r32/runner_r32.py`

```diff
--- review42/scripts/harness-r32/runner_r32.py
+++ review43/scripts/harness-r32/runner_r32.py
@@ -93,3 +93,3 @@
 PY = SI.PY
-TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}
+TREES = {"baseline": "C:/t/iso/frozen-r13/backend", "candidate": "C:/t/iso/cand-r30n/backend"}
 CAPS = dict(PF.PLAN_CAPS)
```

### `harness-r32/sandbox_child_r32.py`

```diff
--- review42/scripts/harness-r32/sandbox_child_r32.py
+++ review43/scripts/harness-r32/sandbox_child_r32.py
@@ -1,3 +1,3 @@
-"""ORCH-05.1 sandbox ingestion CHILD: runs inside the frozen baseline tree (C:/t/iso/frozen-r12/backend, B's code at
-3d5607d) with every root pointed at the sandbox. It creates the schema (the application's own upgrade_to_head), the
+"""ORCH-05.1 sandbox ingestion CHILD: runs inside the frozen baseline tree (C:/t/iso/frozen-r13/backend, B's code at
+7ec3d2c) with every root pointed at the sandbox. It creates the schema (the application's own upgrade_to_head), the
 projects, and registers each staged file as a PENDING index row exactly as document_sync.sync's new-file branch does
@@ -23,3 +23,3 @@
 TREE = pathlib.Path(os.getcwd())
-assert TREE.as_posix().lower() == "c:/t/iso/frozen-r12/backend", TREE
+assert TREE.as_posix().lower() == "c:/t/iso/frozen-r13/backend", TREE
 sys.path.insert(0, str(TREE))
```

### `harness-r32/sandbox_ingest_r32.py`

```diff
--- review42/scripts/harness-r32/sandbox_ingest_r32.py
+++ review43/scripts/harness-r32/sandbox_ingest_r32.py
@@ -38,3 +38,3 @@
 STAGE_FILES = pathlib.Path("C:/t/r2x/r32-stage/files")
-BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")
+BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r13/backend")
 HERE = pathlib.Path(__file__).resolve().parent
```

### `harness-r32/score_lane_r32.py`

```diff
--- review42/scripts/harness-r32/score_lane_r32.py
+++ review43/scripts/harness-r32/score_lane_r32.py
@@ -2,3 +2,3 @@
 
-Usage (cwd C:/t/iso/cand-r29/backend, AI disabled, read-only use of the tree):
+Usage (cwd C:/t/iso/cand-r30n/backend, AI disabled, read-only use of the tree):
   score_lane_r32.py <lane> <rows.json abs> <policy|none> <truth json abs> <run set json abs> <requests json abs> <out json abs>
```

### `harness-r32/test_capture_store.py` (CRLF on disk in both; shown with LF)

```diff
--- review42/scripts/harness-r32/test_capture_store.py
+++ review43/scripts/harness-r32/test_capture_store.py
@@ -1,2 +1,2 @@
-"""R31-04 capture-store contract, at the provider layer (no database, no model). Run from C:/t/iso/cand-r29/backend with
+"""R31-04 capture-store contract, at the provider layer (no database, no model). Run from C:/t/iso/cand-r30n/backend with
 PYTHONPATH including this folder: python -m pytest -q <this file> -p no:cacheprovider"""
```

### `harness-r32/test_portability_r42.py`

```diff
--- review42/scripts/harness-r32/test_portability_r42.py
+++ review43/scripts/harness-r32/test_portability_r42.py
@@ -135,3 +135,3 @@
     ok = {"PATH": f"C:/Windows;{PF.ISOLATION_VENV}/Scripts", "X": "C:/t/r2x/r42-sandbox/x", "H": PF.HERE.as_posix()}
-    assert PF.verify_isolation("C", ok, None, path_entries=[PF.ISOLATION_VENV + "/Lib/site-packages", "C:/t/iso/cand-r29/backend"], modules={})["ok"]
+    assert PF.verify_isolation("C", ok, None, path_entries=[PF.ISOLATION_VENV + "/Lib/site-packages", "C:/t/iso/cand-r30n/backend"], modules={})["ok"]
     for env in ({"DATA_ROOT": "G:/dev (2)/dev/ep-platform-merged/data"}, {"PATH": "C:/Windows;G:\\dev (2)\\dev\\ep-platform-merged\\tools\\claude-2.1.289"},
@@ -150,3 +150,3 @@
         model_fields = {"cache_root": None, "uploads_root": None, "n": None}
-        model_config = {"env_file": "C:/t/iso/cand-r29/backend/.env"}
+        model_config = {"env_file": "C:/t/iso/cand-r30n/backend/.env"}
 
@@ -165,3 +165,3 @@
 def test_the_frozen_trees_settings_never_read_the_merged_env_file():
-    for tree in ("C:/t/iso/frozen-r12/backend", "C:/t/iso/cand-r29/backend"):
+    for tree in ("C:/t/iso/frozen-r13/backend", "C:/t/iso/cand-r30n/backend"):
         src = (pathlib.Path(tree) / "app/core/config.py").read_text(encoding="utf-8")
```

### `harness-r32/test_request_paths_r39.py`

```diff
--- review42/scripts/harness-r32/test_request_paths_r39.py
+++ review43/scripts/harness-r32/test_request_paths_r39.py
@@ -20,3 +20,3 @@
 HERE = pathlib.Path(__file__).resolve().parent
-TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}
+TREES = {"baseline": "C:/t/iso/frozen-r13/backend", "candidate": "C:/t/iso/cand-r30n/backend"}
 # Every provider-calling function the over-approximating static graph reaches from a lane's entry point, with its status
```

### `harness-r32/test_run_control_r38.py`

```diff
--- review42/scripts/harness-r32/test_run_control_r38.py
+++ review43/scripts/harness-r32/test_run_control_r38.py
@@ -3,3 +3,3 @@
 the per-document recorder (nothing skipped silently), the identity rule of the stop controller, the dry stub's injections
-and the probe's sample. Runs from C:/t/iso/cand-r29/backend (the capture store imports app.ai.provider; read-only use).
+and the probe's sample. Runs from C:/t/iso/cand-r30n/backend (the capture store imports app.ai.provider; read-only use).
 ORCH-08C: the declaration check at the gate (undeclared task kind, missing / stale context -> contract breach, the run
```

### `harness-r32/test_unread_pages_r39.py`

```diff
--- review42/scripts/harness-r32/test_unread_pages_r39.py
+++ review43/scripts/harness-r32/test_unread_pages_r39.py
@@ -26,3 +26,3 @@
     out = root / "PROBE.json"
-    r = subprocess.run([SI.PY, str(HERE / "unread_pages_probe_r39.py"), str(out)], cwd="C:/t/iso/cand-r29/backend", env=env, capture_output=True, text=True)
+    r = subprocess.run([SI.PY, str(HERE / "unread_pages_probe_r39.py"), str(out)], cwd="C:/t/iso/cand-r30n/backend", env=env, capture_output=True, text=True)
     assert r.returncode == 0, r.stderr[-2000:]
```

### `harness-r32/tripwire_r32.py`

```diff
--- review42/scripts/harness-r32/tripwire_r32.py
+++ review43/scripts/harness-r32/tripwire_r32.py
@@ -3,3 +3,3 @@
 facts_from_row(EV, row, ai_context, doc_key): the emitted facts of one application row, by the FROZEN evaluator .10
-emission functions (scripts.m2_eval6 record_groups / observation_groups / ai_groups of C:/t/iso/cand-r29, imported
+emission functions (scripts.m2_eval6 record_groups / observation_groups / ai_groups of C:/t/iso/cand-r30n, imported
 read-only), flattened to {"page", "field", "value", "state", "reader", "layer"}; only the three fields.
@@ -22,3 +22,3 @@
 
-CAND_BACKEND = "C:/t/iso/cand-r29/backend"
+CAND_BACKEND = "C:/t/iso/cand-r30n/backend"
 FIELDS = ("identity", "revision", "decision")
```

### `harness-r32/unread_pages_probe_r39.py`

```diff
--- review42/scripts/harness-r32/unread_pages_probe_r39.py
+++ review43/scripts/harness-r32/unread_pages_probe_r39.py
@@ -1,2 +1,2 @@
-"""ORCH-08C (R39-06, task item 2): a CHILD process run inside the candidate tree (C:/t/iso/cand-r29/backend, read-only use)
+"""ORCH-08C (R39-06, task item 2): a CHILD process run inside the candidate tree (C:/t/iso/cand-r30n/backend, read-only use)
 by test_unread_pages_r39.py: Verification 39's scenarios reproduced with the candidate's OWN reader and budget, no
@@ -16,3 +16,3 @@
 TREE = pathlib.Path(os.getcwd())
-assert TREE.as_posix().lower() == "c:/t/iso/cand-r29/backend", TREE
+assert TREE.as_posix().lower() == "c:/t/iso/cand-r30n/backend", TREE
 assert os.environ.get("AI_ENABLED") == "false"
```

