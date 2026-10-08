"""ORCH-05.1 (Review 33 C-5): the frozen inputs of the r32 harness, their paths and their sha256.

Every loader re-hashes the file it reads and refuses a difference ("PACKET MISMATCH"). Nothing here writes anywhere.
File metadata (EP number, relative path, staged sha256) is used only as a KEY, never as label evidence.
ORCH-10 (R42): PILOT names the MERGED installation (the Desktop installation the review39 copy named is absent); every
input file and every sha256 is unchanged (the merged copies are byte-identical). sha256_file opens through the
extended-length prefix (LongPathsEnabled = 0 on this machine: an ordinary open fails at 260 characters)."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

PILOT = pathlib.Path("G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot")
LONG = "\\\\?\\"
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
STAGE = pathlib.Path("C:/t/r2x/r32-stage")
AI_LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
CANDIDATE = pathlib.Path("C:/t/iso/cand-r30n")
BASELINE = pathlib.Path("C:/t/iso/frozen-r13")
CANDIDATE_HEAD = "436daef215c72fbe2429dcd783e087bf39756ad7"
BASELINE_HEAD = "7ec3d2cf983b70a604844beda8eb6b1ec6173d34"

INPUTS = {
    "reviewed2_labels": (PILOT / "fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json",
                         "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    "reviewed2_field_population": (PILOT / "fresh-cohort-r32-reviewed-2/FIELD-POPULATION.json",
                                   "799a4b8f97c4560a2906da84f94515711cf9841b3bb3a9529ad6f5cde338539e"),
    "reviewed2_manifest": (PILOT / "fresh-cohort-r32-reviewed-2/evidence/EVIDENCE-MANIFEST.json",
                           "1f27a544fa9fb839f5ae9bed721f1e00e7d5cbe1f63f56dd5bbf6fa8086bdb76"),
    "packet_manifest": (PILOT / "fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json",
                        "15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed"),
    "renders": (PILOT / "fresh-cohort-r32/RENDERS.json", "175a3a10ac871540dbbeb87f1ec7d2e68b369186d05a60bf5dd751b18e51e8be"),
    "source_manifest": (PILOT / "fresh-cohort-r32/SOURCE-MANIFEST.json", "951e8697a69c3576c24ecdaf0b28de563d35ae7e99addca1fc60e3992df0e259"),
    "frozen_selection": (PILOT / "fresh-cohort-r32/FROZEN-SELECTION.json", "bf71779a612afb1207ac96cb7925979ae3682ea815d137b05eab8968212a5d21"),
    "project_verification": (PILOT / "fresh-cohort-r32/PROJECT-VERIFICATION.json", "4cecf2fca13fe9d46eb1aa2f547b58fe5b584fea46446ca4597cda44dabdf1c4"),
    "evidence_index": (PILOT / "fresh-cohort-r32/EVIDENCE-INDEX.json", "0d0db4f8dbb0143cd4756986024dd43c531ffee2f17a1dd784e9d4bd32ba08b8"),
    "conventions": (PILOT / "fresh-cohort-r32/LABEL-CONVENTIONS-R32.md", "5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570"),
    "drafting_helpers_dir": (PILOT / "fresh-cohort-r32/scripts/lib", None),
    "review31_manifest": (PILOT / "review31/evidence/EVIDENCE-MANIFEST.json", "d5fe164918741014ded7425cda7679bd310a97b07511dd85bb65ec642077c460"),
    "review33": (MR / "reviews/M2-review-33/INDEPENDENT-REVIEW.md", "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804"),
    "policy": (MR / "AI-ACCURACY-POLICY.md", "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47"),
    "policy_amendment": (MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6"),
}

REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"


class PacketMismatch(RuntimeError):
    pass


def long_path(path) -> str:
    """ORCH-10 (R42): the extended-length form of an absolute path, so no path length limit applies to a hash."""
    s = os.path.abspath(str(path)).replace("/", "\\")
    return s if s.startswith(LONG) else LONG + s


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(long_path(path), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_sha(name: str) -> str | None:
    return INPUTS[name][1]


def load(name: str, *, check: bool = True):
    path, expected = INPUTS[name]
    if check and expected is not None:
        got = sha256_file(path)
        if got != expected:
            raise PacketMismatch(f"PACKET MISMATCH: {name} {path} sha256 {got} != {expected}")
    if str(path).endswith(".json"):
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return pathlib.Path(path).read_text(encoding="utf-8")


def load_all(check: bool = True) -> dict:
    """The four inputs the adapter needs, hash-checked."""
    return {"reviewed2": load("reviewed2_labels", check=check), "renders": load("renders", check=check),
            "source_manifest": load("source_manifest", check=check), "selection": load("frozen_selection", check=check),
            "verification": load("project_verification", check=check)}
