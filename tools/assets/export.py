"""Export chosen textures, fonts and audio from the game's Unity files.

Read-only on the game: writes PNG / TTF / WAV into the output folder.
Usage: python -I export.py <Windose_Data> <inventory.json> <out_dir> <spec.json>
spec.json: {"textures": [names or "prefix*"], "fonts": [...], "audio": [...]}
"""
import json
import os
import sys
from collections import defaultdict

import UnityPy

data_dir, inv_path, out_dir, spec_path = sys.argv[1:5]
inv = json.load(open(inv_path, encoding="utf-8"))
spec = json.load(open(spec_path, encoding="utf-8"))
os.makedirs(out_dir, exist_ok=True)


def wanted(name, patterns):
    for p in patterns:
        if p.endswith("*") and name.startswith(p[:-1]):
            return True
        if name == p:
            return True
    return False


kinds = {"Texture2D": spec.get("textures", []), "Font": spec.get("fonts", []), "AudioClip": spec.get("audio", [])}
# One source per (type, name): prefer the non-bundle copy.
chosen = {}
for row in inv:
    t, n = row.get("type"), row.get("name")
    if t in kinds and n and wanted(n, kinds[t]):
        key = (t, n)
        if key not in chosen or chosen[key]["file"].endswith(".bundle"):
            chosen[key] = row

by_file = defaultdict(list)
for row in chosen.values():
    by_file[row["file"]].append(row)

aa = os.path.join(data_dir, "StreamingAssets", "aa", "StandaloneWindows64")
done, failed = 0, []
for fname, rows in by_file.items():
    path = os.path.join(aa if fname.endswith(".bundle") else data_dir, fname)
    env = UnityPy.load(path)
    ids = {r["path_id"]: r for r in rows}
    for obj in env.objects:
        if obj.path_id not in ids:
            continue
        row = ids[obj.path_id]
        d = obj.read()
        try:
            if row["type"] == "Texture2D":
                d.image.save(os.path.join(out_dir, row["name"] + ".png"))
            elif row["type"] == "Font":
                data = bytes(d.m_FontData)
                ext = ".otf" if data[:4] == b"OTTO" else ".ttf"
                open(os.path.join(out_dir, row["name"] + ext), "wb").write(data)
            elif row["type"] == "AudioClip":
                for sname, sdata in d.samples.items():
                    open(os.path.join(out_dir, row["name"] + ".wav"), "wb").write(sdata)
                    break
            done += 1
        except Exception as exc:
            failed.append((row["type"], row["name"], repr(exc)[:150]))
print("exported", done, "of", len(chosen))
for f in failed[:20]:
    print("FAIL", f)
