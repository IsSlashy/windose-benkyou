"""Step 2: French JLPT Tango N4/N3/N2 deck, exported as an .apkg.

In the scratch collection (never the user's profile):
  - VocabDef and SentEng become French (from tr_out); the English goes to the new
    fields VocabDef_EN and SentEng_EN and shows in a closed "English" box;
  - the back shows the French sentence at once (it was a "Reveal English" hint);
  - the template's global CSS reset is scoped to the card, so it cannot reach the
    Windose windows that share the review page;
  - decks become "JLPT Tango::1. N4", "::2. N3", "::3. N2", so studying the parent
    takes N4 first, then N3, then N2.
Usage: build_tango_fr.py <work dir> <tr_out dir> <out.apkg>
"""
import glob
import json
import os
import sys

from anki.collection import Collection, ExportAnkiPackageOptions

work, tr_dir, out_apkg = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")

col = Collection(os.path.join(work, "tango.anki2"))
records = {r["nid"]: r for r in json.load(open(os.path.join(work, "tango_notes.json"), encoding="utf-8"))}
tr = {}
for path in glob.glob(os.path.join(tr_dir, "batch_*.part*.json")):
    for item in json.load(open(path, encoding="utf-8")):
        tr[int(item["id"])] = item
missing = [nid for nid in records if nid not in tr]
assert not missing, f"{len(missing)} notes have no translation"

# ── note type ─────────────────────────────────────────────────────────────────
m = col.models.by_name("Japanese sentences")
names = [f["name"] for f in m["flds"]]
for name in ("VocabDef_EN", "SentEng_EN"):
    if name not in names:
        col.models.add_field(m, col.models.new_field(name))

ENGLISH_BOX = ('\n            {{#VocabDef_EN}}\n            <details class="wb-en">\n'
               '                <summary>English</summary>\n'
               '                <div>{{VocabDef_EN}}</div>\n'
               '                {{#SentEng_EN}}<div class="wb-en-sent">{{SentEng_EN}}</div>{{/SentEng_EN}}\n'
               '            </details>\n            {{/VocabDef_EN}}')
changes = []
for t in m["tmpls"]:
    for key in ("qfmt", "afmt"):
        text = t[key]
        before = text
        text = text.replace('<div class="ensentence" lang="en">{{hint:SentEng}}</div>',
                            '<div class="ensentence" lang="fr">{{SentEng}}</div>')
        if 'class="wb-en"' not in text:
            text = text.replace('<div class="definitions">{{edit:furigana:VocabDef}}</div>',
                                '<div class="definitions">{{edit:furigana:VocabDef}}</div>' + ENGLISH_BOX)
        text = text.replace('<details open class="notes">', '<details class="notes">')
        text = text.replace("&sl=ja&tl=en", "&sl=ja&tl=fr")
        if text != before:
            changes.append(f"{t['name']}.{key}")
        t[key] = text

RESET = "*,\n*::before,\n*::after {"
SCOPED = ".wrap,\n.wrap *,\n.wrap *::before,\n.wrap *::after {"
if RESET in m["css"]:
    m["css"] = m["css"].replace(RESET, SCOPED, 1)
    changes.append("css reset scoped")
assert "\n*,\n*::before" not in m["css"], "global reset still there"
col.models.update_dict(m)
print("note type:", changes)

# ── notes ─────────────────────────────────────────────────────────────────────
notes = []
for nid, r in records.items():
    note = col.get_note(nid)
    t = tr[nid]
    note["VocabDef_EN"] = r["VocabDef"]
    note["SentEng_EN"] = r["SentEng"]
    note["VocabDef"] = t["def_fr"].strip()
    note["SentEng"] = (t.get("sent_fr") or "").strip()
    notes.append(note)
col.update_notes(notes)
print("notes translated:", len(notes))

# ── decks ─────────────────────────────────────────────────────────────────────
RENAME = {"Tango N4": "JLPT Tango::1. N4", "Tango N3": "JLPT Tango::2. N3", "Tango N2": "JLPT Tango::3. N2"}
for old, new in RENAME.items():
    did = col.decks.id_for_name(old)
    if did:
        col.decks.rename(did, new)
default = col.decks.get(1)
print("decks:", [d.name for d in col.decks.all_names_and_ids()])
for new in RENAME.values():
    did = col.decks.id_for_name(new)
    print(" ", new, len(col.find_cards(f"did:{did}")), "cards")

# Check one card renders with the French text.
cid = col.find_cards('"deck:JLPT Tango::1. N4"', order="c.due")[0]
out = col.get_card(cid).render_output()
a = out.answer_text
print("render: french sentence", "lang=\"fr\"" in a, "| english box", "wb-en" in a,
      "| hint gone", "{{hint" not in a and 'class="hint"' not in a)
col.close()

# ── export ────────────────────────────────────────────────────────────────────
col = Collection(os.path.join(work, "tango.anki2"))
if os.path.exists(out_apkg):
    os.remove(out_apkg)
n = col.export_anki_package(out_path=out_apkg, limit=None, options=ExportAnkiPackageOptions(
    with_scheduling=False, with_deck_configs=False, with_media=True, legacy=False))
print("exported", n, "notes ->", out_apkg, os.path.getsize(out_apkg), "bytes")
col.close()
