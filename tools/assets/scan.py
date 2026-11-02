"""List textures, sprites, fonts and audio clips in the game's Unity files.

Read-only: opens the game files, writes one JSON inventory to the output path.
Usage: python -I scan.py <Windose_Data dir> <out.json>
"""
import json
import os
import sys

import UnityPy

data_dir, out_path = sys.argv[1], sys.argv[2]
targets = [os.path.join(data_dir, n) for n in os.listdir(data_dir)
           if n.endswith(".assets") or n.startswith("level") and "." not in n]
aa = os.path.join(data_dir, "StreamingAssets", "aa", "StandaloneWindows64")
targets += [os.path.join(aa, n) for n in os.listdir(aa)
            if n.endswith(".bundle") and not n.startswith("picturetextures")]

inventory = []
for path in targets:
    try:
        env = UnityPy.load(path)
    except Exception as exc:
        inventory.append({"file": os.path.basename(path), "error": repr(exc)})
        continue
    for obj in env.objects:
        kind = obj.type.name
        if kind not in ("Texture2D", "Sprite", "Font", "AudioClip", "VideoClip"):
            continue
        try:
            d = obj.read()
            name = getattr(d, "m_Name", "") or getattr(d, "name", "")
            row = {"file": os.path.basename(path), "type": kind, "name": name, "path_id": obj.path_id}
            if kind == "Texture2D":
                row["size"] = [d.m_Width, d.m_Height]
            elif kind == "AudioClip":
                row["len"] = round(getattr(d, "m_Length", 0) or 0, 2)
            inventory.append(row)
        except Exception as exc:
            inventory.append({"file": os.path.basename(path), "type": kind, "error": repr(exc)[:120]})

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(inventory, fh, ensure_ascii=False, indent=0)
by_type = {}
for r in inventory:
    by_type[r.get("type", "error")] = by_type.get(r.get("type", "error"), 0) + 1
print(len(targets), "files scanned;", by_type)
