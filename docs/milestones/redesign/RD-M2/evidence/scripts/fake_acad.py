"""Stand-in for the Core Console in harness rehearsals: echoes the script, prints this
run's OK marker with the script's own counts (or FAIL when FAKE_ACAD_MODE=fail)."""
import os
import re
import sys

copy, script = sys.argv[1], sys.argv[2]
text = open(script, encoding="utf-8").read()
print(text)
nonce = re.search(r'\(setq ep_nonce "([0-9a-f]+)"', text).group(1)
ins, dele = re.search(r"\(/= ep_ins (\d+)\) \(/= ep_del (\d+)\)", text).groups()
missing = "RDM2-MISSING-BLOCK" in text
if os.environ.get("FAKE_ACAD_MODE") == "fail" or missing:
    print("EP-RD" + "-FAIL:" + nonce + ":insert:rdm2-missing-block")
    print("EP-RD" + "-NOSAVE:" + nonce)
else:
    with open(copy, "ab") as f:
        f.write(b"EDITED")
    print("EP-RD" + "-OK:" + nonce + ":" + ins + ":" + dele)
