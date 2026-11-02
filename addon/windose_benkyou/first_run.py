"""First run on a new PC: imports the decks that Installer.cmd left in user_files/setup.

The installer copies the .apkg files there. On the next profile open the add-on
calls run(): it imports only the decks the collection does not have yet, names the
Kaishi deck, gives JLPT Tango its own preset, suspends the Tango words Kaishi
already teaches (tag doublon_kaishi) and writes setup/done.json. The .apkg files
are deleted afterwards. A PC that already has the decks only loses the copies.

No aqt import here, so the logic can be tested with the plain anki package.
"""
import json
import os
import re
import time

from anki.collection import ImportAnkiPackageOptions, ImportAnkiPackageRequest

KAISHI = "Kaishi 1.5k"
TANGO = "JLPT Tango"
TANGO_LEVELS = ("JLPT Tango::1. N4", "JLPT Tango::2. N3", "JLPT Tango::3. N2")
PACKAGES = (("kaishi", "Kaishi.1.5k.fr.apkg"), ("tango", "jlpt_tango_fr.apkg"))
TANGO_NEW_PER_DAY = 10
TANGO_REVIEWS_PER_DAY = 200


def pending(setup_dir):
    """The packages waiting in setup_dir, in import order (Kaishi first)."""
    out = []
    for kind, name in PACKAGES:
        path = os.path.join(setup_dir, name)
        if os.path.isfile(path):
            out.append((kind, path))
    return out


def _import(col, path):
    before = col.note_count()
    col.import_anki_package(ImportAnkiPackageRequest(package_path=path, options=ImportAnkiPackageOptions(
        with_scheduling=False, with_deck_configs=False, merge_notetypes=False)))
    return col.note_count() - before


def _has_kaishi(col):
    if col.decks.id_for_name(KAISHI):
        return True
    deck = col.decks.get(1, default=False)  # the French Kaishi deck lands in the default deck
    return bool(deck) and col.decks.card_count(1, include_subdecks=False) >= 1000


def _name_kaishi(col):
    deck = col.decks.get(1, default=False)
    if deck and not col.decks.id_for_name(KAISHI) and col.decks.card_count(1, include_subdecks=False) >= 1000:
        col.decks.rename(deck, KAISHI)


def _tango_preset(col):
    conf = next((c for c in col.decks.all_config() if c["name"] == TANGO), None)
    if conf is None:
        conf = col.decks.get_config(col.decks.add_config_returning_id(TANGO))
    conf["new"]["perDay"] = TANGO_NEW_PER_DAY
    conf["rev"]["perDay"] = TANGO_REVIEWS_PER_DAY
    col.decks.update_config(conf)
    for name in (TANGO,) + TANGO_LEVELS:
        deck = col.decks.by_name(name)
        if deck:
            deck["conf"] = conf["id"]
            col.decks.save(deck)


def _hira(text):
    out = []
    for ch in text:
        if 0x30A1 <= ord(ch) <= 0x30F6:
            ch = chr(ord(ch) - 0x60)
        if "ぁ" <= ch <= "ゖ":
            out.append(ch)
    return "".join(out)


def _plain(text):
    return re.sub(r"<[^>]+>|\[\d+\]", "", text or "").replace("&nbsp;", " ").strip()


_FURIGANA = re.compile(r" ?([^ >]+?)\[(.+?)\]")


def _furigana_readings(field_html):  # same rules as the add-on's quiz and sovits_voicegen
    text = re.sub(r"<br\s*/?>", "|", field_html or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ")
    text = re.sub(r"\([^)]*\)|（[^）]*）|＜[^＞]*＞", "", text)
    out = []
    for variant in re.split(r"\s*[/／・]\s*(?![^\[]*\])", text):
        pieces, pos = [], 0
        for m in _FURIGANA.finditer(variant):
            pieces.append([variant[pos:m.start()]])
            pieces.append([a.strip() for a in re.split(r"[|、,，;]", m.group(2)) if a.strip()] or [""])
            pos = m.end()
        pieces.append([variant[pos:]])
        combos = [""]
        for alts in pieces:
            combos = [c + a for c in combos for a in alts][:6]
        out += [_hira(c) for c in combos if _hira(c)]
    return out


def _suspend_kaishi_doubles(col):
    """Tango notes whose word and reading Kaishi already teaches: suspended, tagged doublon_kaishi."""
    known = set()
    for nid in col.find_notes(f'"deck:{KAISHI}"'):
        note = col.get_note(nid)
        if "Word" in note.keys() and "Word Reading" in note.keys():
            readings = re.sub(r"\([^)]*\)|（[^）]*）", " ", _plain(note["Word Reading"]))
            for r in re.split(r"[、,/;・\s]+", readings):
                if _hira(r):
                    known.add((_plain(note["Word"]), _hira(r)))
    doubles = []
    for nid in col.find_notes(f'"deck:{TANGO}"'):
        note = col.get_note(nid)
        if "VocabKanji" not in note.keys():
            continue
        word = _plain(note["VocabKanji"])
        if any((word, r) in known for r in _furigana_readings(note["VocabFurigana"])):
            doubles.append(nid)
    if doubles:
        col.sched.suspend_cards(col.find_cards(" or ".join(f"nid:{nid}" for nid in doubles)))
        col.tags.bulk_add(doubles, "doublon_kaishi")
    return len(doubles)


def run(col, setup_dir):
    """Imports what is missing and returns a report dict (also saved as setup/done.json)."""
    report = {"date": time.strftime("%Y-%m-%d %H:%M"), "imported": {}, "skipped": []}
    for kind, path in pending(setup_dir):
        if kind == "kaishi":
            if _has_kaishi(col):
                report["skipped"].append(KAISHI)
            else:
                report["imported"][KAISHI] = _import(col, path)
            _name_kaishi(col)
        elif kind == "tango":
            if col.decks.id_for_name(TANGO):
                report["skipped"].append(TANGO)
            else:
                report["imported"][TANGO] = _import(col, path)
                _tango_preset(col)
                report["doublon_kaishi"] = _suspend_kaishi_doubles(col)
    report["decks"] = {}
    for name in (KAISHI,) + TANGO_LEVELS:
        did = col.decks.id_for_name(name)
        if did:
            report["decks"][name] = len(col.find_cards(f"did:{did} -is:suspended"))
    for _kind, path in pending(setup_dir):
        os.remove(path)
    with open(os.path.join(setup_dir, "done.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report


def summary(report):
    """One short French message for the user."""
    lines = []
    for name, notes in report.get("imported", {}).items():
        lines.append(f"{name} : {notes} notes importées.")
    if report.get("doublon_kaishi"):
        lines.append(f"{report['doublon_kaishi']} mots que Kaishi enseigne déjà sont mis de côté "
                     "(étiquette doublon_kaishi).")
    if report.get("skipped"):
        lines.append("Déjà dans Anki, pas réimporté : " + ", ".join(report["skipped"]) + ".")
    head = "Paquets de cartes installés." if report.get("imported") else "Rien de nouveau à importer."
    return head + ("\n\n" + "\n".join(lines) if lines else "")
