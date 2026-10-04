"""RD-M2: update the three test_redesign.py assertions that encoded behaviour the owner reversed."""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
R = [
    ("""    assert '(entdel (handent "5DD03"))' in script and "BEEF" not in script""",
     """    # erased only after it is checked to be the symbol meant (RD-M2); a symbol inside a block is not erased
    assert '(if (not ep_failed) (ep_erase "5DD03" nil nil nil 0.010000 "#1"))' in script and "BEEF" not in script
    assert "(entdel (entlast))" not in script and "(entdel (handent" not in script"""),
    ("""    assert '"_.-INSERT" "HEAT DETECTOR" "_S" 1.0 (list 1.000000 2.000000 0.0) 90.000000' in script""",
     """    assert '(command "_.-INSERT" "HEAT DETECTOR" "_S" 1.0 (list 1.000000 2.000000 0.0) 90.000000)' in script"""),
    ("""    assert script.rstrip().endswith("_.QSAVE\\n_.QUIT\\n_Y") or "_.QSAVE" in script""",
     """    # saved only when no step failed (RD-M2): never a bare QSAVE line
    assert '(if (not ep_failed) (progn (command "_.QSAVE") (setq ep_saved T)))' in script
    assert "_.QSAVE" not in script.splitlines()
    assert script.rstrip().endswith("_.QUIT\\n_Y")"""),
    ("""    # proposed review changes are drawn; proposed modules wait for the engineer
    placed = {"insert": {"block": "CR"}, "remove": None}
    assert R._drawn({**placed, "status": "proposed"})
    assert not R._drawn({**placed, "status": "proposed", "source": "interface"})
    assert R._drawn({**placed, "status": "approved", "source": "interface"})""",
     """    # only a change the engineer approved is drawn, of the review or a module alike (platform owner, RD-M2)
    placed = {"insert": {"block": "CR"}, "remove": None}
    assert not R._drawn({**placed, "status": "proposed"})
    assert not R._drawn({**placed, "status": "proposed", "source": "interface"})
    assert R._drawn({**placed, "status": "approved", "source": "interface"})
    assert R._drawn({**placed, "status": "approved"})"""),
    ("""    assert '(if (tblsearch "BLOCK" "CR") "CR" "CR=C:/lib/CR.dwg")' in inserts[0]""",
     """    # from this installation's library, never the path the change stored (RD-M1 F001, RD-M2)
    here = (R.LIBRARY / "CR.dwg").resolve().as_posix()
    assert f'(if (tblsearch "BLOCK" "CR") "CR" "CR={here}")' in inserts[0]
    assert "C:/lib" not in script and change["insert"]["library"] == "C:/lib/CR.dwg"      # the stored value kept"""),
]
for a, b in R:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", p)
