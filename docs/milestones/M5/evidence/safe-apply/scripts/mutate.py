"""Temporary mutations of wt-m5's service.py for the M5 mutation evidence
(ORCH-039). `python mutate.py lock|copy-in-lock|restore`. The original is
saved beside this script and restored byte for byte (sha256 checked)."""
import hashlib
import shutil
import sys
from pathlib import Path

SERVICE = Path("G:/dev (2)/dev/ep-platform-merged/wt-m5/backend/app/redesign/service.py")
SAVED = Path(__file__).with_name("service.py.orig")

LOCKED = '''    db.rollback()  # discard the read transaction used by verification
    if db.get_bind().dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
        row = db.get(ProjectRedesign, row_id, populate_existing=True)
    else:
        row = (db.query(ProjectRedesign).filter(ProjectRedesign.id == row_id)
               .with_for_update().one_or_none())'''
UNLOCKED = '''    db.expire_all()  # MUTATION M5-M1: the lock removed (the pre-RDM2-R1 read)
    row = db.get(ProjectRedesign, row_id)'''

STAGED_OUTSIDE = '''        staged = _stage(Path(run.copy), dest)        # the slow copy, before the lock (U2M5-02/04)'''
STAGED_DEFERRED = '''        staged = dest.with_name(f".{dest.name}{PART}")  # MUTATION M5-M2: the copy moved inside the lock'''
FINALIZE = '''                _finalize(staged, dest)
                published = True'''
FINALIZE_WITH_COPY = '''                _stage(Path(run.copy), dest)  # MUTATION M5-M2: the slow copy inside the lock
                _finalize(staged, dest)
                published = True'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(what: str) -> None:
    if what == "restore":
        shutil.copyfile(SAVED, SERVICE)
        print("restored", sha(SERVICE))
        return
    if not SAVED.exists():
        shutil.copyfile(SERVICE, SAVED)
    text = SAVED.read_text(encoding="utf-8")
    if what == "lock":
        assert text.count(LOCKED) == 1
        text = text.replace(LOCKED, UNLOCKED)
    elif what == "copy-in-lock":
        assert text.count(STAGED_OUTSIDE) == 1 and text.count(FINALIZE) == 1
        text = text.replace(STAGED_OUTSIDE, STAGED_DEFERRED).replace(FINALIZE, FINALIZE_WITH_COPY)
    else:
        raise SystemExit(f"unknown mutation {what}")
    SERVICE.write_bytes(text.encode("utf-8"))
    print("mutated", what, "original", sha(SAVED), "mutant", sha(SERVICE))


if __name__ == "__main__":
    main(sys.argv[1])
