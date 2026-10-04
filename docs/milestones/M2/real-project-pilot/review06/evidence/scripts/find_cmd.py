import json, sys
path = r"C:/Users/moham/.claude/projects/c--Users-moham-Desktop-dev-dev/be7878a4-f3f7-49c7-8971-5873084fd122.jsonl"
key = sys.argv[1]
hits = []
for line in open(path, encoding="utf-8"):
    if key not in line:
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    content = obj.get("message", {}).get("content", [])
    if not isinstance(content, list):
        continue
    for c in content:
        if isinstance(c, dict) and c.get("type") == "tool_use":
            cmd = json.dumps(c.get("input", {}))
            if key in cmd:
                hits.append(c.get("input", {}).get("command") or c.get("input", {}).get("content") or cmd)
print(len(hits))
for h in hits[-int(sys.argv[2]) if len(sys.argv) > 2 else -1:]:
    print("=====")
    print(h[:4000])
