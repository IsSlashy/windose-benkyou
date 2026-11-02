"""Tests first_run.run() on a brand new collection, then a second time (must skip)."""
import os
import shutil
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
addon, kaishi_apkg, tango_apkg, work = sys.argv[1:5]
sys.path.insert(0, addon)
import first_run  # noqa: E402
from anki.collection import Collection  # noqa: E402

shutil.rmtree(work, ignore_errors=True)
setup = os.path.join(work, "setup")
os.makedirs(setup)


def stage():
    shutil.copy(kaishi_apkg, os.path.join(setup, "Kaishi.1.5k.fr.apkg"))
    shutil.copy(tango_apkg, os.path.join(setup, "jlpt_tango_fr.apkg"))


col = Collection(os.path.join(work, "collection.anki2"))
print("fresh decks:", [d.name for d in col.decks.all_names_and_ids()])
stage()
print("pending:", [k for k, _ in first_run.pending(setup)])
t = time.time()
report = first_run.run(col, setup)
print(f"run 1 ({time.time() - t:.0f}s):", report)
print(first_run.summary(report))
print("left in setup:", sorted(os.listdir(setup)))
print("decks:", sorted(d.name for d in col.decks.all_names_and_ids()))
for name in ("Kaishi 1.5k", "JLPT Tango", "JLPT Tango::1. N4"):
    conf = col.decks.config_dict_for_deck_id(col.decks.id_for_name(name))
    print(f"  preset {name}: {conf['name']} new/day {conf['new']['perDay']} rev/day {conf['rev']['perDay']}")
print("note types:", sorted(m.name for m in col.models.all_names_and_ids()))
first = col.find_cards('"deck:Kaishi 1.5k" is:new', order="c.due")[:1]
print("first Kaishi card:", col.get_card(first[0]).note()["Word"] if first else None)
media = os.path.join(work, "collection.media")
print("media files:", len(os.listdir(media)))

stage()
report2 = first_run.run(col, setup)
print("run 2:", report2)
print(first_run.summary(report2))
print("left in setup:", sorted(os.listdir(setup)))
print("notes total:", col.note_count())
col.close()
