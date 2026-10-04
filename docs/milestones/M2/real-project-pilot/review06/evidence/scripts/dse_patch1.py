import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/services/design_sheet_extractor.py")
s = p.read_text(encoding="utf-8")
old = "            if line.catalog_no and line.quantity and (line.catalog_confidence is None or line.catalog_confidence < RECHECK_QUANTITY_BELOW):"
new = "            if line.catalog_no and line.quantity and (line.catalog_confidence is None or line.catalog_confidence < CONFIRM_CATALOG_BELOW):"
assert s.count(old) == 1
s = s.replace(old, new)
old2 = "RECHECK_QUANTITY_BELOW = 90\n"
assert s.count(old2) == 1
s = s.replace(old2, old2 + "# Part numbers read by the strip under this confidence get the independent passes (_confirm_catalog). A separate\n# knob from the recheck of quantities (M2 review 06, section 5), so the part gate can be measured on its own.\nCONFIRM_CATALOG_BELOW = RECHECK_QUANTITY_BELOW\n")
p.write_text(s, encoding="utf-8")
print("ok")
