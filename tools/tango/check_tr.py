import json, glob, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
src = {}
for f in sorted(glob.glob("tr_in/batch_*.json")):
    for it in json.load(open(f, encoding="utf-8")):
        src[it["id"]] = it
out = {}
dup = 0
for f in sorted(glob.glob("tr_out/batch_*.part*.json")):
    for it in json.load(open(f, encoding="utf-8")):
        if it["id"] in out: dup += 1
        out[it["id"]] = it
missing = [i for i in src if i not in out]
extra = [i for i in out if i not in src]
c = collections.Counter()
bad = []
for i, s in src.items():
    o = out.get(i)
    if not o: continue
    d, t = o.get("def_fr", ""), o.get("sent_fr", "")
    if not d.strip(): c["empty_def"] += 1
    if "—" in d + t or "–" in d + t: c["dash"] += 1
    if s["en"].strip() and not t.strip(): c["en_but_no_fr"] += 1; bad.append(("nofr", s["word"]))
    if ("<b>" in s["jp"]) and s["en"].strip() and "<b>" not in t: c["b_lost"] += 1; bad.append(("b", s["word"], t))
    if d.strip() == s["def"].strip() and re.search(r"[a-z]{4}", d): c["def_unchanged"] += 1; bad.append(("same", s["word"], d))
    if re.search(r"\b(the|to be|of the|and)\b", d): c["english_in_def"] += 1; bad.append(("en?", s["word"], d))
print("src", len(src), "out", len(out), "dup", dup, "missing", len(missing), "extra", len(extra), dict(c))
for b in bad[:25]: print(b)
