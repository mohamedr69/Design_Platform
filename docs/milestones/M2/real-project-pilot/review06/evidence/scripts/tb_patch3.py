import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\title_block.py")
s = p.read_text(encoding="utf-8")
old = '''    data = image_to_data(image, output_type="dict")
    groups: dict = {}
    for i, word in enumerate(data["text"]):
        if not str(word).strip() or float(data["conf"][i]) < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x0, y0 = data["left"][i] / scale + clip.x0, data["top"][i] / scale + clip.y0
        x1, y1 = x0 + data["width"][i] / scale, y0 + data["height"][i] / scale
        g = groups.setdefault(key, [x0, y0, x1, y1, []])
        g[0], g[1], g[2], g[3] = min(g[0], x0), min(g[1], y0), max(g[2], x1), max(g[3], y1)
        g[4].append(str(word).strip())
    return [Line(g[0], g[1], g[2], g[3], " ".join(g[4])) for g in groups.values()]'''
new = r'''    data = image_to_data(image, output_type="dict")
    words: dict = {}
    for i, word in enumerate(data["text"]):
        if not str(word).strip() or float(data["conf"][i]) < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x0, y0 = data["left"][i] / scale + clip.x0, data["top"][i] / scale + clip.y0
        words.setdefault(key, []).append((x0, y0, x0 + data["width"][i] / scale, y0 + data["height"][i] / scale, str(word).strip()))
    out = []
    for line in words.values():
        # Tesseract joins neighbouring cells of a row into one line ("SCALE 1:150 @ A0 Drg. no. REV."): split
        # where the gap between two words is wider than about one word-height, so each cell is a run of its own.
        line.sort(key=lambda w: w[0])
        run = [line[0]]
        for w in line[1:]:
            height = max(run[-1][3] - run[-1][1], w[3] - w[1], 1.0)
            if w[0] - run[-1][2] > 1.1 * height:
                out.append(run)
                run = []
            run.append(w)
        out.append(run)
    lines = []
    for run in out:
        text = " ".join(w[4] for w in run).strip(" )(|[]{}'\"`~,;")
        if text:
            lines.append(Line(min(w[0] for w in run), min(w[1] for w in run), max(w[2] for w in run), max(w[3] for w in run), text))
    return lines'''
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok")
