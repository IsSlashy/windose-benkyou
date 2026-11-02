"""Step 3: import the French JLPT Tango deck into Ramy's Anki profile (Anki must be closed).

  - backs up collection.anki2 first;
  - imports the .apkg without scheduling (all cards new);
  - gives the JLPT Tango decks their own preset: 10 new cards a day, N4 then N3 then N2;
  - suspends the Tango cards whose word and reading Kaishi already teaches, tagged
    doublon_kaishi (Browse, tag:doublon_kaishi, Unsuspend to bring them back).
Usage: install_tango.py <profile dir> <apkg> <backup dir>
"""
import os
import re
import shutil
import sys
import time

from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest

profile, apkg, backup_dir = sys.argv[1:4]
sys.stdout.reconfigure(encoding="utf-8")
path = os.path.join(profile, "collection.anki2")
os.makedirs(backup_dir, exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
for suffix in ("", "-wal"):
    if os.path.exists(path + suffix):
        shutil.copy2(path + suffix, os.path.join(backup_dir, f"collection-{stamp}.anki2{suffix}"))
print("backup:", os.path.join(backup_dir, f"collection-{stamp}.anki2"))

col = Collection(path)
try:
    if col.decks.id_for_name("JLPT Tango"):
        print("JLPT Tango already there: no import")
    else:
        before = col.note_count()
        res = col.import_anki_package(ImportAnkiPackageRequest(package_path=apkg, options=ImportAnkiPackageOptions(
            with_scheduling=False, with_deck_configs=False, merge_notetypes=False)))
        print("imported notes:", col.note_count() - before)

    # Preset: the same daily rhythm on the parent and the three levels.
    kaishi_did = col.decks.id_for_name("Kaishi 1.5k")
    kaishi_conf = col.decks.config_dict_for_deck_id(kaishi_did) if kaishi_did else None
    if kaishi_conf:
        print("Kaishi preset:", kaishi_conf["name"], "new/day", kaishi_conf["new"]["perDay"],
              "reviews/day", kaishi_conf["rev"]["perDay"])
    conf = next((c for c in col.decks.all_config() if c["name"] == "JLPT Tango"), None)
    if conf is None:
        conf = col.decks.add_config_returning_id("JLPT Tango")
        conf = col.decks.get_config(conf)
    conf["new"]["perDay"] = 10
    conf["rev"]["perDay"] = 200
    col.decks.update_config(conf)
    for name in ("JLPT Tango", "JLPT Tango::1. N4", "JLPT Tango::2. N3", "JLPT Tango::3. N2"):
        deck = col.decks.by_name(name)
        deck["conf"] = conf["id"]
        col.decks.save(deck)
    print("preset JLPT Tango: new/day 10, reviews/day 200")

    # Words Kaishi already teaches (same word, same reading).
    def hira(text):
        out = []
        for ch in text:
            if 0x30A1 <= ord(ch) <= 0x30F6:
                ch = chr(ord(ch) - 0x60)
            if "ぁ" <= ch <= "ゖ":
                out.append(ch)
        return "".join(out)

    def plain(text):
        return re.sub(r"<[^>]+>|\[\d+\]", "", text or "").replace("&nbsp;", " ").strip()

    known = set()
    for nid in col.find_notes('"deck:Kaishi 1.5k"'):
        n = col.get_note(nid)
        if "Word" in n.keys():
            for r in re.split(r"[、,/;・\s]+", re.sub(r"\([^)]*\)|（[^）]*）", " ", plain(n["Word Reading"]))):
                if hira(r):
                    known.add((plain(n["Word"]), hira(r)))
    furigana = re.compile(r" ?([^ >]+?)\[(.+?)\]")

    def furigana_readings(field_html):  # same rules as sovits_voicegen and the add-on
        text = re.sub(r"<br\s*/?>", "|", field_html or "", flags=re.I)
        text = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ")
        text = re.sub(r"\([^)]*\)|（[^）]*）|＜[^＞]*＞", "", text)
        out = []
        for variant in re.split(r"\s*[/／・]\s*(?![^\[]*\])", text):
            pieces, pos = [], 0
            for m in furigana.finditer(variant):
                pieces.append([variant[pos:m.start()]])
                pieces.append([a.strip() for a in re.split(r"[|、,，;]", m.group(2)) if a.strip()] or [""])
                pos = m.end()
            pieces.append([variant[pos:]])
            combos = [""]
            for alts in pieces:
                combos = [c + a for c in combos for a in alts][:6]
            out += [hira(c) for c in combos if hira(c)]
        return out

    dupes = []
    for nid in col.find_notes('"deck:JLPT Tango"'):
        n = col.get_note(nid)
        word = plain(n["VocabKanji"])
        if any((word, r) in known for r in furigana_readings(n["VocabFurigana"])):
            dupes.append(nid)
    cids = col.find_cards(" or ".join(f"nid:{nid}" for nid in dupes)) if dupes else []
    if cids:
        col.sched.suspend_cards(cids)
        col.tags.bulk_add(dupes, "doublon_kaishi")
    print("already in Kaishi, suspended:", len(dupes), "notes,", len(cids), "cards")

    for name in ("JLPT Tango::1. N4", "JLPT Tango::2. N3", "JLPT Tango::3. N2"):
        did = col.decks.id_for_name(name)
        total = len(col.find_cards(f"did:{did}"))
        active = len(col.find_cards(f"did:{did} -is:suspended"))
        print(f"  {name}: {total} cards, {active} to study")
    first = col.find_cards('"deck:JLPT Tango::1. N4" is:new -is:suspended', order="c.due")[:1]
    if first:
        note = col.get_card(first[0]).note()
        sound = re.search(r"\[sound:([^\]]+)\]", note["VocabAudio"])
        media_ok = bool(sound) and os.path.exists(os.path.join(col.media.dir(), sound.group(1)))
        print("first new card:", note["VocabKanji"], "| audio in media:", media_ok)
finally:
    col.close()
print("done")
