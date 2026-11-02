"""Step 1: import Ankidrone Essentials V9 into a scratch collection, keep N4, N3, N2 only.

Writes:
  <work>/tango.anki2           scratch collection with decks "Tango N4", "Tango N3", "Tango N2"
  <work>/tango_notes.json      one record per note, for translation and voices
Never touches the user's Anki profile.
"""
import json
import os
import shutil
import sys

from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest

apkg, work = sys.argv[1], sys.argv[2]
sys.stdout.reconfigure(encoding="utf-8")
os.makedirs(work, exist_ok=True)
path = os.path.join(work, "tango.anki2")
for p in (path, path + "-wal", os.path.join(work, "tango.media")):
    if os.path.isdir(p):
        shutil.rmtree(p)
    elif os.path.exists(p):
        os.remove(p)

col = Collection(path)
col.import_anki_package(ImportAnkiPackageRequest(package_path=apkg, options=ImportAnkiPackageOptions(
    with_scheduling=False, with_deck_configs=False, merge_notetypes=False)))

KEEP = {"2. JLPT Tango N4": "Tango N4", "3. JLPT Tango N3": "Tango N3", "4. JLPT Tango N2": "Tango N2"}
parent = None
for d in col.decks.all_names_and_ids():
    if d.name == "Ankidrone Essentials V9":
        parent = d.id
for d in list(col.decks.all_names_and_ids()):
    leaf = d.name.split("::")[-1]
    if d.name.startswith("Ankidrone Essentials V9::") and leaf in KEEP:
        deck = col.decks.get(d.id)
        deck["name"] = KEEP[leaf]
        col.decks.save(deck)
# Everything else from the package goes: N5 (Kaishi covers it), N1, the README.
for d in list(col.decks.all_names_and_ids()):
    if d.name.startswith("Ankidrone Essentials V9"):
        col.decks.remove([d.id])
info = col.models.by_name("Ankidrone Info")
if info and not col.models.use_count(info):
    col.models.remove(info["id"])

nt = col.models.by_name("Japanese sentences")
records = []
for name in ("Tango N4", "Tango N3", "Tango N2"):
    did = col.decks.id_for_name(name)
    cids = col.find_cards(f'"deck:{name}"', order="c.due, c.ord")
    seen = set()
    for cid in cids:
        card = col.get_card(cid)
        if card.nid in seen:
            continue
        seen.add(card.nid)
        note = card.note()
        rec = {"nid": note.id, "deck": name, "suspended": card.queue == -1}
        rec.update({k: note[k] for k in note.keys()})
        records.append(rec)
    print(name, "cards", len(cids), "notes", len(seen))
with open(os.path.join(work, "tango_notes.json"), "w", encoding="utf-8") as fh:
    json.dump(records, fh, ensure_ascii=False)
print("notes total", len(records), "note types", [m["name"] for m in col.models.all()])
print("decks", [d.name for d in col.decks.all_names_and_ids()])
col.close()
