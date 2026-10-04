# Adapter contract: `r32-labels-reviewed-2` → r32 truth (`labels_adapter_r32.py`)

Correction package **review33** (task ORCH-05.1), answering Review 33 condition C-5 (findings R33-05, R33-07) and populating the attributes that condition C-4 needs.

**Reference set:** `r32-labels-reviewed-2`, sha256 `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6`. The reference set is independently AI-reviewed (Claude agents) and not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).

**Code:** `scripts/harness-r32/labels_adapter_r32.py`, with 13 tests in `tests/test_labels_adapter_r32.xml`.

**Output:** `dry-run/TRUTH-R32.json`. Its hash is recorded in `dry-run/DRY-RUN-REPORT.json` (`truth_sha256`).

## 1. Inputs

The adapter reads only these inputs. Each is re-hashed before it is read, and any difference raises `PACKET MISMATCH` (`inputs_r32.py`).

| Input | Use | sha256 |
|---|---|---|
| `fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json` | page-field rows, document reviews, aliases, convention rulings | `89c60e9d…b9a6` |
| `fresh-cohort-r32/SOURCE-MANIFEST.json` | `ep`, `relative_path` and `staged_sha256`. Used as **keys only**, never as label evidence | `951e8697…e259` |
| `fresh-cohort-r32/RENDERS.json` | `pages_in_scope` and `page_count` | `175a3a10…e8be` |
| `fresh-cohort-r32/FROZEN-SELECTION.json` | the `stratum`, `how` and `selection_order` of each pool document | `bf71779a…5d21` |
| `fresh-cohort-r32/PROJECT-VERIFICATION.json` | `results[ep].contractor` | `4cecf2fc…f1c4` |

## 2. Schema of `build_truth(...)`

```
{"schema": "r32-truth-1", "source_version": "r32-labels-reviewed-2",
 "aliases": {"F031": "F001", "F052": "F038", "F059": "F046", "F070": "F067"},
 "compilations": ["F002", "F035", "F043", "F069"], "layout_rules": [...],
 "documents": {pool_id: DOCUMENT}, "rows": {"<pool_id>|<page>|<field>": ROW}}
```

**ROW**, one per labelled (pool id, page, field). There are 432 in all: 144 labelled pages × 3 fields.

- **Copied verbatim:** `state`, `association`, `literal`, `class` (decision only), `actor`, `actor_state`, `absent_kind`, `location`, `printed_label`, `semantic_role`, `excluded_from_scoring`, `review_status`.
- **Converted or derived:**
  - `resubmission_required` becomes a bool;
  - `candidates` holds the literals;
  - `doc_resolved_for_scoring` and `doc_carries_fact` come from the document review of that field;
  - `alternates` and `alternate_kinds`;
  - `evaluator_decision`;
  - `count_once_alias_of`.
- **`truth_kind`:** one of `value`, `absent` or `not_scorable`, together with `scorable` and `not_scorable_reasons`.

**DOCUMENT** fields:

- **Identity and aliases:** `pool_id`, `canonical_id`, `is_alias`, `alias_kind`.
- **Project and file keys:** `ep`, `project` (`EP-<ep>`), `contractor`, `doc_key` (`EP-<ep>/<relative_path>`), `relative_path`, `staged_sha256`.
- **Selection:** `stratum`, `how`, `selection_order`.
- **Pages:** `in_scope_pages`, `page_count`, `labelled_pages`, `compilation`.
- **Classification:** `layout_key`, `layout_rule`, `kind`, `decision_type`, `decision_control`.
- **Review:** `independent_review` (true), and `fields[f]`, which holds `resolved_for_scoring`, `carries_fact`, `primary` and `has_fact`.

## 3. The three truth values and NOT_SCORABLE

`truth_of(row)` returns exactly one of the following. They are never confused with each other.

| Return value | When |
|---|---|
| the **literal** (str) | `state` present, `association` resolved, `excluded_from_scoring` false, `review_status` not unresolved, **and** the document's `resolved_for_scoring` for **this field** is `yes` |
| `ABSENT` (sentinel) | `state` absent, and the document field is resolved |
| `NOT_SCORABLE` (sentinel) | every other row |
| `None` | from `lookup(...)` only: there is **no row** (a page beyond the reader scope, or an alias without labels of its own) |

`NOT_SCORABLE` and `ABSENT` are module singletons. They are falsy, they survive pickling as themselves, and neither is `None`.

A row is NOT_SCORABLE when any of the following reasons applies. The reasons are listed on the row.

| Reason | Source rule |
|---|---|
| `ambiguous`, `illegible`, `unsupported` (state) | frozen conventions §2; Review 33 §5.1 |
| `uncertain_association` (present + association uncertain) | conventions §2 and §4 "embedded only"; rulings (f), (g), (g2) |
| `excluded_from_scoring` | Review 33 §4.1 and §4.2 (F069 p1/p3, F019 p1) |
| `review_status_unresolved` | reviewed-1 handling, kept as a guard (none in reviewed-2) |
| `document_field_resolved_for_scoring=<x>` (≠ yes) | the per-field document resolution (R33-05). **Every** row of that field in that document is excluded |

**Result on reviewed-2:**

- **Total:** 32 NOT_SCORABLE rows, on 32 pages, in 25 documents.
  - By field: 9 identity, 11 revision and 12 decision.
  - By reason (the reasons overlap): uncertain association 21, ambiguous 9, excluded 3, and document field not resolved 14.
- **Comparison with Review 33's count:** Review 33 §2 counted 30 rows on 30 pages in 25 documents.
  - The two extra rows are **F069 p2 and p4 identity**. Both are `absent` pages of a document whose identity is `resolved_for_scoring: no` (Review 33 §4.1).
  - The adapter excludes them, which is conservative. The alternative would let an identity asserted on a continuation page be scored as a false positive against a field that Review 33 ruled unresolved for the document.
- **Totals by kind:** value 252, absent 148, not scorable 32.

**F019 and F069 count as unresolved truth, per field.**

- F019 revision is NOT_SCORABLE. F019 identity and decision stay scorable.
- F069 identity is NOT_SCORABLE on all four pages. F069 revision and decision stay scorable (both absent).

## 4. Mapping decisions

1. **Per-field resolution (R33-05).**
   - `primary(pool, f)` is the document's own `review.f.resolved_for_scoring == "yes"`. It is never one flag for the whole document.
   - `has_fact(pool, f)` requires `carries_fact == "yes"` as well.
   - `population()` reproduces `FIELD-POPULATION.json` exactly: identity 57, revision 38, decision 38. The id lists are identical, and a test checks this.
2. **Count-once aliases.**
   - Aliases (`count_once_aliases`) are F031→F001 and F059→F046 (Review 33 (c)(ii)), and F052→F038 and F070→F067 (frozen §1).
   - Each alias keeps its own rows, flagged `count_once_alias_of`. Its document has `is_alias` true and is **never** primary and never counted.
   - F052 and F070 have no rows of their own. Nothing is invented for them, and they take the canonical document's layout key.
3. **Compilations ((h)).**
   - The compilation documents are those named in the reviewed-2 convention ruling "(h) compilation files": F002, F035, F043 and F069.
   - Truth is always keyed by (pool id, page). No file-level value exists anywhere in the schema.
4. **Either-form identity ((g)(1)).**
   - Where the same page's revision row has `semantic_role` "labelled revision appended to the submittal reference", the printed form with its tail (taken from the revision row's `printed_label`, for example `B01-ASC-SD-ELE-0102-Rev.00`) is added to the identity row's `alternates`.
   - This applies to 12 rows: F008, F009, F013, F020, F021, F028, F030, F032, F034 and F036 on page 3, and F025 and F037 on page 2.
5. **Unlabelled suffix base form (an interpretation, open for ORCH-05R).**
   - Where the same page's revision row has `semantic_role` "suffix of the printed document number" (frozen §4 "embedded only"; ruling (g)(2)), the identity without its unlabelled `- R0n` suffix is added to `alternates`. For example, `NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002- R00` gains `…-0002`.
   - This applies to 8 rows: F003, F004, F005, F006 (p1 and p2), F007, F011 and F015.
   - **Why it is accepted.**
     - It carries the frozen evaluator .10 identity equivalence (`m2_pilot_eval.same_identity` → `suffix`), which the Review 31 rules consumed.
     - The application files a trailing `-Rn` as the revision (`split_suffix`).
     - Scoring the base number as a **wrong** identity would make a critical acceptance on resolved truth in B, and so an INVALID comparison, on 7 documents (8 rows), from a convention that rules only the revision row.
   - **Status.** It is recorded in `alternate_kinds` and is not a label change. The independent review may reject it. Removing it is a one-line change in `_suffix_base`.
6. **Decision.**
   - The `class` is kept. `evaluator_decision` maps it to the application vocabulary: approved → `approved`, approved as noted → `ANN`, revise and resubmit → `rejected`, rejected → `rejected`. The application files revise-and-resubmit, resubmit and not approved all as `rejected` (`evidence_reader.EVIDENCE_OPTIONS`, `document_control._OPTIONS`).
   - `resubmission_required` is set on 9 rows ((d1)), 8 of them outside aliases.
7. **Document attributes (C-4).**
   - `project` is `EP-<ep>`.
   - `contractor` is the `PROJECT-VERIFICATION.json results[ep].contractor`. The cohort has 6 projects and 6 distinct contractors, so this leg equals the project leg here.
   - `stratum` and `how` come from `FROZEN-SELECTION.json pool`. All 72 documents have them: review_signal 40, drawing_signal 20, other 12.
   - `decision_type` is the sorted set of `class` values on the document's **scorable** present decision rows, joined with `+`, or `none`. On canonical documents: approved as noted 31, approved 4, revise and resubmit 3, none 30.
   - `decision_control` is one of:
     - `positive`: the decision carries the fact (38);
     - `negative`: the decision is resolved and **every** in-scope decision row is a scorable ABSENT, with `blank_decision_area` or `no_decision_area` (29);
     - `none`: anything else (1, F067, whose decision is ambiguous).

## 5. Layout / template key (deterministic rule)

`layout_key(kind, page1_role, pool_id)` searches the lower-cased text `"<kind>\n<page 1 page_role>"`. Both strings are the reviewed labels' own descriptions of the page images. File and folder names are never used. The **first** matching rule wins. A document that matches no rule is its own family, `single:<pool id>`. An alias with no pages takes its canonical document's key.

| # | Source | Key | Pattern | Documents |
|---|---|---|---|---|
| 1 | helper `emaar.py` | `emaar-mirage-document-submittal` | `emaar / mirage document submittal` | F008 F009 F013 F020 F021 F025 F028 F030 F032 F034 F036 F037 |
| 2 | helper `dewan.py` | `pivot-al-arabia-shop-drawing-dewan-stamp` | `pivot / al arabia electrical shop drawing` | F010 F012 F017 F018 F019 F022 F026 F033 |
| 3 | helper `arex.py` | `arex-enco-shop-drawing-approval-request` | `shop drawing approval request` | F039 F040 |
| 4 | helper `enco.py` | `enco-shop-drawing` | `(^|\n)enco shop drawing` | F041 F046 F050 F056 F057 F058 F059 F060 |
| 5 | helper `infinity.py` | `infinity-al-arabia-drawing-sheet` | `infinity engineering consultants / al arabia drawing sheet` | F042 F044 F047 F048 F049 F051 F053 F054 |
| 6 | kind | `dewan-design-drawing-civil-defence-stamp` | `civil defence approved dewan design drawing` | F014 F016 |
| 7 | kind | `dewan-material-submittal-form` | `material submittal form, submission sheet` | F001 F031 |
| 8 | kind | `lacasa-shop-drawing-submittal-form` | `shop drawing submittal form` | F003 F004 F005 F007 F011 F015 |
| 9 | kind | `contractor-reply-to-comments-sheet` | `reply to consultant comments` | F024 F029 |
| 10 | kind | `al-arabia-document-transmittal` | `document transmittal` | F062 F063 |
| 11 | kind | `ajman-civil-defence-approval-letter` | `civil defence approval letter` | F038 (F052) |
| — | none | `single:<id>` | — | F002 F006 F023 F027 F035 F043 F045 F055 F061 F064 F065 F066 F067 (F070) F068 F069 F071 F072 |

**Where the rules come from:**

- **Rules 1–5** are the fixed `page_role` and `kind` strings written by the five drafting helpers in `fresh-cohort-r32/scripts/lib/`. That is the helper provenance. Those files are bound in `BINDING-MANIFEST-R33.json`.
- **Rules 6–11** name the other families that the reviewed labels' `kind` text shows to have two or more members.

**Correlation with project.** The layout key is correlated with project, because each project has its own consultant templates. It is a finer partition, though: 3563 splits into three families, 26687 into three, 29255 into three, and 15744 is all singletons.

## 6. What the adapter does not do

- It never changes a label value.
- It never reads an image, a prediction or an earlier label set (r26.2 was not opened).
- It never treats a file name as evidence.
- It never writes anything. `prepare_r33.py` writes its output.
