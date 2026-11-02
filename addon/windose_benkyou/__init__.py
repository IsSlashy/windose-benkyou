"""Windose Benkyou: Anki dressed as Windose 20, the desktop from NEEDY GIRL OVERDOSE.

Every picture, font and sound comes from files already on this PC: textures and
fonts exported from the installed game, and sounds from the Opera GX pack made
earlier. They are for personal use only: do not share or publish this folder.

Inside the app: web/*.css restyle the deck list, overview, card and bottom bar;
web/home.js adds the taskbar and a working Start menu; web/quiz.js asks for the
meaning and the reading before the answer is shown; web/stream.js adds KAngel's
stream window and its chat to the review screen.
Around the app: the Windose title bar colours, menu bar, heart icon and title.
Disabling this add-on restores the plain look.
"""

import ctypes
import difflib
import hashlib
import html
import json
import os
import re
import sys
import unicodedata

from anki import hooks as anki_hooks
from aqt import gui_hooks, mw
from aqt.qt import QFontDatabase, QIcon, QPixmap, QTimer
from aqt.reviewer import Reviewer

try:
    import winsound
except ImportError:  # not on Windows: stay silent
    winsound = None

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_ID = os.path.basename(ADDON_DIR)
WEB = f"/_addons/{ADDON_ID}/web"
FONTS = os.path.join(ADDON_DIR, "web", "fonts")
ASSETS = os.path.join(ADDON_DIR, "web", "assets")
SOUNDS = os.path.join(ADDON_DIR, "sounds")
VOICES = os.path.join(ADDON_DIR, "user_files", "voices")
DEV_DIR = os.path.join(ADDON_DIR, "dev")
DEV_FLAG = os.path.join(ADDON_DIR, "dev_tour.flag")

# Colours measured on the game's window and button textures.
INK = "#4d23cf"      # window outline
SHADE = "#815cdd"    # button shadow
TITLE = "#f0d1f1"    # title bar
FACE = "#f7e1fb"     # button and taskbar face

WALLPAPERS = {"windose": None, "nso": "wall_nso.jpg"}
MILESTONES = (10, 25, 50, 100, 150, 200, 300)
AGAIN, GOOD = 1, 3

mw.addonManager.setWebExports(__name__, r"web/.*\.(css|js|ttf|otf|png|jpg)")


def _config():
    conf = mw.addonManager.getConfig(__name__) or {}
    sounds = {"start": "piporo", "correct": "poko", "again": "sippai", "learn": "status_up",
              "milestone": "Tetehen"}
    sounds.update(conf.get("sound_files") or {})
    fields = {"word": "Word", "meaning": "Word Meaning", "reading": "Word Reading",
              "sentence": "Sentence", "sentence_furigana": "Sentence Furigana",
              "sentence_meaning": "Sentence Meaning", "notes": "Notes"}
    fields.update(conf.get("quiz_fields") or {})
    return {
        "simple_mode": conf.get("simple_mode", True),
        "character": conf.get("character", "kangel") if conf.get("character") in ("kangel", "ame") else "kangel",
        "voice": "original" if conf.get("voice") == "original" else "character",
        "quiz": conf.get("quiz", True),
        "quiz_fields": fields,
        "wallpaper": conf.get("wallpaper", "windose"),
        "taskbar": conf.get("taskbar", True),
        "stream": conf.get("stream", True),
        "chat": conf.get("chat", True),
        "sounds": conf.get("sounds", True),
        "sound_files": sounds,
        "window_chrome": conf.get("window_chrome", True),
        "window_title": conf.get("window_title", "べんきょう.exe ♡ Anki"),
        "window_pos": conf.get("window_pos") if isinstance(conf.get("window_pos"), dict) else {},
        "rename_default_deck_to": conf.get("rename_default_deck_to", "Kaishi 1.5k"),
    }


def _dev_log(line):
    if not os.path.isdir(DEV_DIR):
        return
    with open(os.path.join(DEV_DIR, "log.txt"), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# ── inside the app: which screens get which stylesheet ─────────────────────────

P = "html:not(#wb-a):not(#wb-b)"  # outranks Onigiri's late !important rules

SIMPLE_OVERVIEW = f"""<style id="wb-simple">
{P} .onigiri-reviewer-header-buttons > *:not(:first-child):not(.onigiri-reviewer-progress),
{P} .overview-profile-bar,
{P} .onigiri-overview-action-custom-study,
{P} .onigiri-overview-action-description,
{P} .overview-reveal-action {{ display: none !important; }}
</style>"""

SIMPLE_BOTTOM = f"""<style id="wb-simple">
{P} #middle td:nth-child(2),
{P} #middle td:nth-child(4),
{P} td.stat > .onigiri-other-btn {{ display: none !important; }}
</style>"""


def _wallpaper_css(conf):
    image = WALLPAPERS.get(conf["wallpaper"])
    if not image:
        return ""
    return (f"<style id=\"wb-wallpaper\">{P} {{ background: #f9e3ff url('{WEB}/assets/{image}') "
            "center / cover fixed no-repeat !important; }</style>")


PAT_SOUNDS = ("nadenade_1", "nadenade_2")  # the game's head-pat sounds


def _play_file(name):
    if name not in PAT_SOUNDS or not _config()["sounds"] or winsound is None:
        return
    path = os.path.join(SOUNDS, f"{name}.wav")
    if os.path.exists(path):
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as exc:
            _dev_log(f"sound failed: {exc!r}")


def _save_window_pos(value):
    key, _, pos = value.partition(":")
    if key not in ("stream", "chat"):
        return
    conf = mw.addonManager.getConfig(__name__) or {}
    layout = conf.get("window_pos") if isinstance(conf.get("window_pos"), dict) else {}
    if pos == "reset":
        layout.pop(key, None)
    else:
        try:
            x, y = (int(float(v)) for v in pos.split(","))
        except ValueError:
            return
        layout[key] = [x, y]
    conf["window_pos"] = layout
    mw.addonManager.writeConfig(__name__, conf)


def _on_webview_content(web_content, context):
    name = type(context).__name__ if context is not None else "None"
    conf = _config()
    if name in ("DeckBrowser", "Overview"):
        web_content.css += [f"{WEB}/base.css", f"{WEB}/home.css"]
        web_content.body += _wallpaper_css(conf)
        if conf["taskbar"]:
            web_content.body += (f"<script>window.wbCharacter = {json.dumps(conf['character'])};"
                                 f"window.wbVoice = {json.dumps(conf['voice'])};</script>")
            web_content.js.append(f"{WEB}/home.js")
        if name == "Overview" and conf["simple_mode"]:
            web_content.body += SIMPLE_OVERVIEW
    elif name == "Reviewer":
        web_content.css += [f"{WEB}/base.css", f"{WEB}/review.css"]
        web_content.body += _wallpaper_css(conf)
        if conf["quiz"]:
            web_content.js.append(f"{WEB}/quiz.js")
        if conf["stream"]:
            web_content.body += f"<script>window.wbLayout = {json.dumps(conf['window_pos'])};</script>"
            web_content.js.append(f"{WEB}/stream.js")
    elif name in ("ReviewerBottomBar", "OverviewBottomBar", "DeckBrowserBottomBar"):
        web_content.css += [f"{WEB}/base.css", f"{WEB}/bars.css"]
        if name == "ReviewerBottomBar" and conf["simple_mode"]:
            web_content.body += SIMPLE_BOTTOM


gui_hooks.webview_will_set_content.append(_on_webview_content)


# ── sounds from the GX pack ────────────────────────────────────────────────────

def _play(event):
    conf = _config()
    if not conf["sounds"] or winsound is None:
        return
    name = conf["sound_files"].get(event)
    path = os.path.join(SOUNDS, f"{name}.wav") if name else ""
    if not path or not os.path.exists(path):
        return
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as exc:
        _dev_log(f"sound failed: {exc!r}")


# ── her voice: the card's audio spoken by KAngel or Ame ───────────────────────
# sovits_voicegen.py (the owner's own GPT-SoVITS models, D:\\TTS) writes one clip per original audio file name into
# user_files/voices/<character>/. When Anki is about to play a card's sound,
# the clip is played instead; if it does not exist, the original plays.

def _voice_clip(name):
    conf = _config()
    if conf["voice"] != "character" or not name:
        return None
    clip = os.path.join(VOICES, conf["character"], hashlib.md5(name.encode("utf-8")).hexdigest()[:20] + ".mp3")
    return clip if os.path.exists(clip) else None


def _media_file_filter(name):
    try:
        return _voice_clip(name) or name
    except Exception:
        return name


anki_hooks.media_file_filter.append(_media_file_filter)


def _set_voice(value):
    conf = mw.addonManager.getConfig(__name__) or {}
    conf["voice"] = "original" if value == "original" else "character"
    mw.addonManager.writeConfig(__name__, conf)


# ── answer mode: check the typed meaning and reading ──────────────────────────

ARTICLES = {"le", "la", "les", "l", "un", "une", "des", "du", "de", "d", "se", "s", "a", "au", "aux"}
KANJI = re.compile(r"[㐀-鿿豈-﫿々]")
VOWEL_ROWS = ["あかがさざただなはばぱまやらわぁゃ", "いきぎしじちぢにひびぴみりぃ",
              "うくぐすずつづぬふぶぷむゆるぅゅゔ", "えけげせぜてでねへべぺめれぇ",
              "おこごそぞとどのほぼぽもよろをぉょ"]


def _plain(text):
    """Field HTML to plain text: no tags, no furigana brackets, entities decoded."""
    text = re.sub(r"<br\s*/?>", ", ", text or "", flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\[sound:[^\]]*\]", " ", text)
    return html.unescape(text).replace("\xa0", " ").strip()


def _fold(text):
    text = unicodedata.normalize("NFKD", text.lower().replace("œ", "oe").replace("æ", "ae"))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _words(text):
    return [w for w in _fold(text).split() if w not in ARTICLES]


def _meaning_options(field_text):
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", _plain(field_text))
    parts = re.split(r"[,;/]| ou ", text)
    return [p for p in (x.strip() for x in parts) if _words(p)]


def _check_meaning(typed, field_text):
    """(ok, close): ok if one typed sense matches one of the card's senses."""
    options = [_words(o) for o in _meaning_options(field_text)]
    tries = [_words(t) for t in re.split(r"[,;/]", typed or "") if _words(t)]
    best = 0.0
    for tw in tries:
        for ow in options:
            if tw == ow or set(ow) <= set(tw):
                return True, False
            if set(tw) <= set(ow) and len("".join(tw)) >= 3:
                return True, False
            best = max(best, difflib.SequenceMatcher(None, " ".join(tw), " ".join(ow)).ratio())
    return (best >= 0.85), (best >= 0.85)


def _hira(text):
    """Kana only, katakana folded to hiragana, ー spelled as the vowel it lengthens."""
    out = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            ch = chr(code - 0x60)
        if "ぁ" <= ch <= "ゖ":
            out.append(ch)
        elif ch == "ー" and out:
            prev = out[-1]
            out.append(next((v for v, row in zip("あいうえお", VOWEL_ROWS) if prev in row), ""))
    return "".join(out)


def _reading_options(field_text):
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]|（[^）]*）", " ", _plain(field_text))
    parts = re.split(r"[、,/;・\s]+", text)
    return [h for h in (_hira(p) for p in parts) if h]


def _furigana_readings(field_html):
    """Every kana reading of a furigana word field, alternatives expanded.

    JLPT Tango writes 開[あ<br>ひら]く, 吃驚[きっきょう、びっくり], 抱[いだ]く/ 抱[だ]く or
    注意[ちゅうい]＜する＞: the readings of 開く are あく and ひらく.
    """
    text = re.sub(r"<br\s*/?>", "|", field_html or "", flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).replace("\xa0", " ")
    text = re.sub(r"\([^)]*\)|（[^）]*）|＜[^＞]*＞|<[^>]*>", "", text)
    out = []
    for variant in re.split(r"\s*[/／・]\s*(?![^\[]*\])", text):
        pieces, pos = [], 0
        for m in FURIGANA.finditer(variant):
            pieces.append([variant[pos:m.start()]])
            pieces.append([a.strip() for a in re.split(r"[|、,，;]", m.group(2)) if a.strip()] or [""])
            pos = m.end()
        pieces.append([variant[pos:]])
        combos = [""]
        for alts in pieces:
            combos = [c + a for c in combos for a in alts][:6]
        for c in combos:
            h = _hira(c)
            if h and h not in out:
                out.append(h)
    return out


# Field names per note type. Kaishi uses the config's quiz_fields; the JLPT Tango
# decks (Ankidrone "Japanese sentences") show a sentence and ask about the word in pink.
NOTE_TYPE_FIELDS = {
    "Japanese sentences": {"word": "VocabKanji", "meaning": "VocabDef", "reading": "VocabFurigana",
                           "sentence": "SentKanji", "sentence_furigana": "SentFurigana",
                           "sentence_meaning": "SentEng", "notes": "", "reading_furigana": True,
                           "in_sentence": True},
}


def _fields_for(note, conf):
    model = note.note_type() or {}
    return NOTE_TYPE_FIELDS.get(model.get("name"), conf["quiz_fields"])


def _note_word(note, f):
    raw = note[f["word"]] if f.get("word") in note.keys() else ""
    return re.sub(r"\[\d+\]", "", _plain(raw)).strip()  # Tango numbers homographs: 思いやり[1]


def _note_readings(note, f):
    raw = note[f["reading"]] if f.get("reading") in note.keys() else ""
    return _furigana_readings(raw) if f.get("reading_furigana") else _reading_options(raw)


def _check_reading(typed, field_text):
    want = _reading_options(field_text)
    got = _hira(typed or "")
    if got and got in want:
        return True, False
    close = any(difflib.SequenceMatcher(None, got, w).ratio() >= 0.8 for w in want) if got else False
    return False, close


# ── the lesson: what KAngel or Ame says when a card is still to learn ─────────

ROMAJI = {}
for _row, _cons in (("あいうえお", ["a", "i", "u", "e", "o"]),
                    ("かきくけこ", ["ka", "ki", "ku", "ke", "ko"]), ("がぎぐげご", ["ga", "gi", "gu", "ge", "go"]),
                    ("さしすせそ", ["sa", "shi", "su", "se", "so"]), ("ざじずぜぞ", ["za", "ji", "zu", "ze", "zo"]),
                    ("たちつてと", ["ta", "chi", "tsu", "te", "to"]), ("だぢづでど", ["da", "ji", "zu", "de", "do"]),
                    ("なにぬねの", ["na", "ni", "nu", "ne", "no"]), ("はひふへほ", ["ha", "hi", "fu", "he", "ho"]),
                    ("ばびぶべぼ", ["ba", "bi", "bu", "be", "bo"]), ("ぱぴぷぺぽ", ["pa", "pi", "pu", "pe", "po"]),
                    ("まみむめも", ["ma", "mi", "mu", "me", "mo"]), ("らりるれろ", ["ra", "ri", "ru", "re", "ro"]),
                    ("ぁぃぅぇぉ", ["a", "i", "u", "e", "o"])):
    ROMAJI.update(zip(_row, _cons))
ROMAJI.update({"や": "ya", "ゆ": "yu", "よ": "yo", "わ": "wa", "を": "o", "ゔ": "vu",
               "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa"})
for _k, _base in (("き", "k"), ("ぎ", "g"), ("に", "n"), ("ひ", "h"), ("び", "b"), ("ぴ", "p"),
                  ("み", "m"), ("り", "r")):
    for _small, _v in (("ゃ", "a"), ("ゅ", "u"), ("ょ", "o")):
        ROMAJI[_k + _small] = _base + "y" + _v
for _k, _base in (("し", "sh"), ("じ", "j"), ("ぢ", "j"), ("ち", "ch")):
    for _small, _v in (("ゃ", "a"), ("ゅ", "u"), ("ょ", "o"), ("ぇ", "e")):
        ROMAJI[_k + _small] = _base + _v
ROMAJI.update({"ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo", "てぃ": "ti", "でぃ": "di",
               "うぃ": "wi", "うぇ": "we", "うぉ": "wo", "ゔぁ": "va", "ゔぃ": "vi", "ゔぇ": "ve", "ゔぉ": "vo"})


def _romaji(text):
    """Hepburn romaji for a kana reading (long vowels written twice)."""
    s, out, i, double = _hira(text), [], 0, False
    while i < len(s):
        if s[i] == "っ":
            double, i = True, i + 1
            continue
        if s[i] == "ん":
            nxt = s[i + 1:i + 2]
            out.append("n'" if nxt and nxt in "あいうえおやゆよ" else "n")
            i += 1
            continue
        piece = ROMAJI.get(s[i:i + 2]) if i + 1 < len(s) else None
        step = 2 if piece else 1
        piece = piece or ROMAJI.get(s[i], "")
        if double and piece:
            piece = ("t" + piece) if piece.startswith("ch") else (piece[0] + piece)
        double = False
        out.append(piece)
        i += step
    return "".join(out)


FURIGANA = re.compile(r" ?([^ >]+?)\[(.+?)\]")


def _segments(field_html):
    """Field HTML with Anki furigana to [text, ruby, bold] segments, other tags dropped."""
    segs, bold = [], False
    for token in re.split(r"(<[^>]+>)", field_html or ""):
        if not token:
            continue
        if token.startswith("<"):
            tag = token.lower()
            if re.match(r"<(b|strong)\b", tag):
                bold = True
            elif re.match(r"</(b|strong)\b", tag):
                bold = False
            elif re.match(r"<br\b", tag):
                segs.append([" ", "", bold])
            continue
        text = html.unescape(token).replace("\xa0", " ")
        pos = 0
        for m in FURIGANA.finditer(text):
            if m.start() > pos:
                segs.append([text[pos:m.start()], "", bold])
            segs.append([m.group(1), m.group(2), bold])
            pos = m.end()
        if pos < len(text):
            segs.append([text[pos:], "", bold])
    return segs


def _first_sentences(text, limit=170):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = max(text.rfind(". ", 0, limit), text.rfind("。", 0, limit))
    return text[:cut + 1] if cut > 40 else text[:limit].rsplit(" ", 1)[0] + "…"


LESSON_LINES = {
    "kangel": {
        "intro": [["いっしょにおぼえよ！", "On l'apprend ensemble !"],
                  ["てんちゃんがおしえてあげる！", "KAngel t'explique !"],
                  ["はじめてはみんなそう！", "La première fois, c'est normal !"]],
        "outro": [["おぼえた？じゃあ次いこっ！",
                   "C'est retenu ? Entrée pour la suivante. Elle reviendra bientôt !"]],
    },
    "ame": {
        "intro": [["だいじょうぶ。あめがおしえる", "pas grave. je t'explique"],
                  ["しらなくてとうぜんだよ", "c'est normal de pas savoir"],
                  ["いっしょにおぼえよ", "on l'apprend ensemble"]],
        "outro": [["おぼえた？じゃ、つぎ", "c'est retenu ? alors Entrée. elle reviendra plus tard"]],
    },
}


def _lesson(note, conf):
    """The card explained in plain French, from its own fields."""
    import random
    f, names = _fields_for(note, conf), note.keys()

    def field(key):
        return note[f[key]] if f.get(key) in names else ""

    char = conf["character"]
    word = _note_word(note, f)
    readings = _note_readings(note, f)
    reading = readings[0] if readings else ""
    lines = []
    if word and reading and KANJI.search(word):
        said = " ou ".join(f"{r} ({_romaji(r)})" for r in readings[:3])  # 開く: あく ou ひらく
        lines.append(f"« {word} » se lit {said}.")
    elif word and reading:
        lines.append(f"« {word} » se prononce « {_romaji(reading)} ».")
    meaning = re.sub(r"\s*;\s*", " ; ", _plain(field("meaning"))).rstrip(". ")
    if meaning[:1].isupper() and not meaning[:2].isupper():
        meaning = meaning[0].lower() + meaning[1:]  # "Je, moi" reads "je, moi" mid-sentence
    if meaning:
        lines.append(f"Ça veut dire : {meaning}.")
    example = _segments(field("sentence_furigana") or field("sentence"))
    note_text = _plain(re.sub(r"<br\s*/?>", " ", field("notes"), flags=re.I))
    voice = LESSON_LINES[char]
    return {
        "char": char,
        "who": "Ame" if char == "ame" else "KAngel",
        "intro": random.choice(voice["intro"]),
        "lines": lines,
        "example": example if any(seg[0].strip() for seg in example) else [],
        # Inline tags (the <b> around the word) go without leaving a space behind.
        "example_fr": re.sub(r"\s{2,}", " ", _plain(re.sub(r"</?(b|i|u|em|strong|span)\b[^>]*>", "",
                                                            field("sentence_meaning"), flags=re.I))),
        "tip": _first_sentences(note_text) if note_text else "",
        "outro": random.choice(voice["outro"]),
    }


_quiz = {"card_id": None, "checks": None, "values": None, "verdict": None, "pending": False}


def _quiz_reset():
    _quiz.update(card_id=None, checks=None, values=None, verdict=None, pending=False)


def _quiz_checks(card, conf):
    """Which answers this card can ask for, or None if its note type has neither field."""
    note = card.note()
    names = note.keys()
    f = _fields_for(note, conf)
    checks = {}
    if f.get("meaning") in names and _meaning_options(note[f["meaning"]]):
        checks["meaning"] = note[f["meaning"]]
    readings = _note_readings(note, f)
    if readings:
        word = _note_word(note, f)
        # A word written only in kana shows its reading already: no need to type it.
        if not word or KANJI.search(word):
            checks["reading"] = "、".join(readings)
    return checks or None


def _judge(values):
    checks = _quiz["checks"] or {}
    skipped = bool(values.get("skipped"))
    result = {"skipped": skipped}
    ok = True
    if "meaning" in checks:
        typed = (values.get("meaning") or "").strip()
        good, close = _check_meaning(typed, checks["meaning"]) if typed else (False, False)
        result["meaning"] = {"typed": typed, "ok": good, "close": close,
                             "expected": _plain(checks["meaning"])}
        ok = ok and good
    if "reading" in checks:
        typed = (values.get("reading") or "").strip()
        good, close = _check_reading(typed, checks["reading"]) if typed else (False, False)
        result["reading"] = {"typed": typed, "ok": good, "close": close and not good,
                             "expected": "、".join(_reading_options(checks["reading"]))}
        ok = ok and good
    result["ok"] = ok and not skipped
    # Not knowing is not failing: "Je ne sais pas", or Enter with nothing typed,
    # means "to learn", in orange, and she explains the card. A wrong answer
    # stays a wrong answer, in red.
    typed_any = any((values.get(k) or "").strip() for k in ("meaning", "reading") if k in checks)
    result["empty"] = not skipped and not typed_any
    result["learn"] = not result["ok"] and (skipped or result["empty"])
    result["ease"] = GOOD if result["ok"] else AGAIN
    result["suggest"] = "Correct" if result["ok"] else ("À apprendre" if result["learn"] else "À revoir")
    if result["learn"]:
        card = getattr(mw.reviewer, "card", None)
        result["lesson"] = _lesson(card.note(), _config()) if card is not None else None
    return result


_original_show_answer = Reviewer._showAnswer
_original_default_ease = Reviewer._defaultEase


def _show_answer(self, *args, **kwargs):
    """Every way of revealing the answer (Enter, Space, the bottom button) checks first."""
    card = getattr(self, "card", None)
    if (card is None or self.state != "question" or _quiz["card_id"] != card.id
            or _quiz["verdict"] is not None):
        return _original_show_answer(self, *args, **kwargs)
    if _quiz["values"] is not None:
        _quiz["verdict"] = _judge(_quiz["values"])
        return _original_show_answer(self, *args, **kwargs)
    if _quiz["pending"]:
        return None

    def got(values):
        _quiz["pending"] = False
        if self.card is None or self.card.id != card.id or self.state != "question":
            return
        _quiz["values"] = values or {}
        _quiz["verdict"] = _judge(_quiz["values"])
        _original_show_answer(self, *args, **kwargs)

    _quiz["pending"] = True
    self.web.evalWithCallback("window.wbQuiz ? window.wbQuiz.values() : null", got)
    return None


def _default_ease(self):
    card = getattr(self, "card", None)
    if card is not None and _quiz["card_id"] == card.id and _quiz["verdict"]:
        return _quiz["verdict"]["ease"]
    return _original_default_ease(self)


Reviewer._showAnswer = _show_answer
Reviewer._defaultEase = _default_ease

SUGGEST_JS = """(function (ease, learn) {
  function go() {
    var b = document.querySelector('button[data-ease="' + ease + '"]');
    if (!b) return;
    document.querySelectorAll('.wb-suggest').forEach(function (x) { x.classList.remove('wb-suggest', 'wb-learn'); });
    b.classList.add('wb-suggest');
    if (learn) {
      b.classList.add('wb-learn');
      var l = b.querySelector('.onigiri-answer-label');
      if (l) l.textContent = 'À apprendre';
    }
    b.focus();
  }
  go(); setTimeout(go, 80); setTimeout(go, 400);
})(%d, %s);"""

VALIDATE_LABEL_JS = """(function () {
  function go() {
    var b = document.getElementById('ansbut');
    if (!b) return;
    var l = b.querySelector('.onigiri-show-answer-label');
    if (l) l.textContent = 'Valider';
    b.setAttribute('data-onigiri-show-answer-label', 'Valider');
  }
  go(); setTimeout(go, 100); setTimeout(go, 500);
})();"""


# ── the stream window: today's numbers, KAngel's mood and the chat ─────────────

_session = {"started": False, "last_count": -1}


def _today():
    """Reviews logged since today's cutoff: all, correct, and 'again'."""
    try:
        cutoff = (mw.col.sched.day_cutoff - 86400) * 1000
        row = mw.col.db.first(
            "select count(), sum(case when ease = 1 then 1 else 0 end) "
            "from revlog where id > ? and ease between 1 and 4", cutoff)
        total, again = int(row[0] or 0), int(row[1] or 0)
        return total, total - again, again
    except Exception:
        return 0, 0, 0


def _on_show_question(card):
    conf = _config()
    total, good, again = _today()
    if not _session["started"]:
        _session["started"] = True
        _play("start")
    elif total != _session["last_count"] and total in MILESTONES:
        _play("milestone")
    _session["last_count"] = total

    _quiz_reset()
    checks = _quiz_checks(card, conf) if conf["quiz"] else None
    if checks:
        _quiz.update(card_id=card.id, checks=checks)
        opts = json.dumps({"needMeaning": "meaning" in checks, "needReading": "reading" in checks,
                           "inSentence": bool(_fields_for(card.note(), conf).get("in_sentence"))})
        mw.reviewer.web.eval(f"window.wbQuiz && window.wbQuiz.ask({opts});")
        mw.reviewer.bottom.web.eval(VALIDATE_LABEL_JS)
        mw.reviewer.web.setFocus()
    else:
        mw.reviewer.web.eval("window.wbQuiz && window.wbQuiz.off();")

    if conf["stream"]:
        payload = json.dumps({"count": total, "good": good, "again": again, "character": conf["character"],
                              "chat": conf["chat"], "simple": conf["simple_mode"]})
        mw.reviewer.web.eval(f"window.wbStream && window.wbStream.update({payload});")


def _on_show_answer(card):
    conf = _config()
    verdict = _quiz["verdict"] if _quiz["card_id"] == card.id else None
    if verdict:
        mw.reviewer.web.eval(f"window.wbQuiz && window.wbQuiz.verdict({json.dumps(verdict)});")
        learn = bool(verdict.get("learn"))
        mw.reviewer.bottom.web.eval(SUGGEST_JS % (verdict["ease"], "true" if learn else "false"))
        _play("correct" if verdict["ok"] else ("learn" if learn else "again"))
    if conf["stream"]:
        mw.reviewer.web.eval("window.wbStream && window.wbStream.phase('a');")
        if verdict:
            mood = "yay" if verdict["ok"] else ("learn" if verdict.get("learn") else "oops")
            line = (verdict.get("lesson") or {}).get("intro")
            mw.reviewer.web.eval(
                f"window.wbStream && window.wbStream.react({json.dumps(mood)}, {json.dumps(line)});")


def _on_answer(reviewer, card, ease):
    conf = _config()
    already = _quiz["card_id"] == card.id and _quiz["verdict"] is not None
    _quiz_reset()
    if already:  # the reaction and the sound came with the result
        return
    _play("again" if ease == 1 else "correct")
    if conf["stream"]:
        mood = "oops" if ease == 1 else "yay"
        reviewer.web.eval(f"window.wbStream && window.wbStream.react({json.dumps(mood)});")


def _on_state_change(new_state, old_state):
    if new_state != "review":
        _session["started"] = False
        _quiz_reset()


gui_hooks.reviewer_did_show_question.append(_on_show_question)
gui_hooks.reviewer_did_show_answer.append(_on_show_answer)
gui_hooks.reviewer_did_answer_card.append(_on_answer)
gui_hooks.state_did_change.append(_on_state_change)


# ── messages from the pages: the answer form and the Start menu ───────────────

def _study():
    """Study the deck picked last (Kaishi or a JLPT Tango level); Kaishi if that deck is empty."""
    did = mw.col.decks.get_current_id()
    if not did or not mw.col.decks.card_count(did, include_subdecks=True):
        target = _config()["rename_default_deck_to"]
        did = mw.col.decks.id_for_name(target) if target else None
        if did:
            mw.col.decks.select(did)
    mw.moveToState("review")


def _open_addons():
    action = getattr(mw.form, "actionAdd_ons", None)
    if action is not None:
        action.trigger()


START_ACTIONS = {
    "study": _study,
    "decks": lambda: mw.moveToState("deckBrowser"),
    "add": lambda: mw.onAddCard(),
    "browse": lambda: mw.onBrowse(),
    "stats": lambda: mw.onStats(),
    "sync": lambda: mw.on_sync_button_clicked(),
    "settings": _open_addons,
    "quit": lambda: mw.close(),
}


def _set_character(key):
    if key not in ("kangel", "ame"):
        return
    conf = mw.addonManager.getConfig(__name__) or {}
    conf["character"] = key
    mw.addonManager.writeConfig(__name__, conf)
    if mw.state == "review" and _config()["stream"]:
        mw.reviewer.web.eval(f"window.wbStream && window.wbStream.setCharacter({json.dumps(key)});")


def _on_js_message(handled, message, context):
    if not isinstance(message, str):
        return handled
    if message.startswith("wbchar:"):
        _set_character(message[len("wbchar:"):])
        return (True, None)
    if message.startswith("wbvoice:"):
        _set_voice(message[len("wbvoice:"):])
        return (True, None)
    if message.startswith("wbsfx:"):
        _play_file(message[len("wbsfx:"):])
        return (True, None)
    if message.startswith("wbpos:"):
        _save_window_pos(message[len("wbpos:"):])
        return (True, None)
    if message.startswith("wbstart:"):
        action = START_ACTIONS.get(message[len("wbstart:"):])
        if action:
            # Run after the click returns, so dialogs do not open inside the bridge call.
            QTimer.singleShot(0, action)
        return (True, None)
    if message.startswith("wbquiz:"):
        try:
            values = json.loads(message[len("wbquiz:"):])
        except ValueError:
            values = {}
        reviewer = mw.reviewer
        card = getattr(reviewer, "card", None)
        if card is not None and _quiz["card_id"] == card.id and reviewer.state == "question":
            _quiz["values"] = values if isinstance(values, dict) else {}
            QTimer.singleShot(0, reviewer._showAnswer)
        return (True, None)
    return handled


gui_hooks.webview_did_receive_js_message.append(_on_js_message)


# ── around the app: title bar, menu bar, icon, title ───────────────────────────

_pixel_family = None


def _load_qt_fonts():
    global _pixel_family
    if _pixel_family is not None:
        return _pixel_family
    _pixel_family = ""
    for fname in ("PixelMplus10-Regular.ttf", "PixelMplus10-Bold.ttf"):
        font_id = QFontDatabase.addApplicationFont(os.path.join(FONTS, fname))
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
        if fname.startswith("PixelMplus10-Regular") and families:
            _pixel_family = families[0]
    return _pixel_family


def _menu_stylesheet(family):
    # PixelMplus10 is drawn on a 10 px grid, so 20 px keeps every pixel sharp.
    font = f'font-family: "{family}"; font-size: 20px;' if family else "font-size: 15px;"
    return f"""
QMenuBar {{
    background: {FACE}; color: {INK}; {font}
    border-top: 2px solid #ffffff; border-bottom: 2px solid {SHADE}; padding: 1px 4px;
}}
QMenuBar::item {{ background: transparent; padding: 3px 10px; margin: 1px 1px; }}
QMenuBar::item:selected {{ background: {TITLE}; color: {INK}; border: 1px dotted {INK}; }}
QMenuBar::item:pressed {{ background: {INK}; color: #ffffff; }}
QMenu {{
    background: {FACE}; color: {INK}; {font}
    border: 2px solid {INK}; padding: 3px;
}}
QMenu::item {{ padding: 4px 26px 4px 22px; background: transparent; }}
QMenu::item:selected {{ background: {INK}; color: #ffffff; }}
QMenu::item:disabled {{ color: #a48bbf; }}
QMenu::separator {{ height: 2px; background: {SHADE}; margin: 4px 8px; }}
"""


def _colorref(hex_color):
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return ctypes.c_uint32(r | (g << 8) | (b << 16))


def _paint_title_bar():
    """Windows 11 lets apps pick the caption, caption text and border colours."""
    if sys.platform != "win32":
        return
    try:
        hwnd = ctypes.c_void_p(int(mw.winId()))
        dwm = ctypes.windll.dwmapi
        for attr, color in ((35, TITLE), (36, INK), (34, INK)):
            value = _colorref(color)
            dwm.DwmSetWindowAttribute(hwnd, ctypes.c_uint32(attr), ctypes.byref(value), ctypes.sizeof(value))
    except Exception as exc:
        _dev_log(f"title bar colour failed: {exc!r}")


def _apply_window_chrome():
    conf = _config()
    if not conf["window_chrome"]:
        return
    family = _load_qt_fonts()
    mw.menuBar().setStyleSheet(_menu_stylesheet(family))
    heart = QPixmap(os.path.join(ASSETS, "heart.png"))
    if not heart.isNull():
        mw.setWindowIcon(QIcon(heart))
    if conf["window_title"]:
        mw.setWindowTitle(conf["window_title"])
    _paint_title_bar()


# ── one-time fix: the French Kaishi deck lands in the default deck ─────────────

def _rename_default_deck():
    target = _config()["rename_default_deck_to"]
    if not target or mw.col is None:
        return
    try:
        deck = mw.col.decks.get(1, default=False)
        if not deck or deck["name"] not in ("Default", "Par défaut"):
            return
        if mw.col.decks.by_name(target):
            return
        if mw.col.decks.card_count(1, include_subdecks=False) < 1000:
            return
        mw.col.decks.rename(deck, target)
        mw.deckBrowser.refresh()
    except Exception as exc:  # never block startup over a cosmetic rename
        _dev_log(f"rename failed: {exc!r}")


# ── dev tour: walks every screen once and saves its state (only if flagged) ───
# It never answers a card, so it leaves no trace in the review history.

TYPE_JS = """(function (m, r) {
  var a = document.getElementById('wb-q-meaning'), b = document.getElementById('wb-q-reading');
  a.value = m; a.dispatchEvent(new Event('input'));
  b.value = r; b.dispatchEvent(new Event('input'));
})(%s, %s);"""


LAYOUT_JS = """(function () {
  function r(e) { if (!e) return null; var b = e.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.bottom)]; }
  var q = document.getElementById('wb-quiz'), a = document.getElementById('qa'), cs = getComputedStyle(document.body);
  return JSON.stringify({quiz: r(q), qa: r(a), qaMarginTop: a && getComputedStyle(a).marginTop,
    quizMarginBottom: q && getComputedStyle(q).marginBottom, display: cs.display, rows: cs.gridTemplateRows,
    justify: cs.justifyContent, align: cs.alignContent, bodyH: cs.height, overflow: cs.overflow,
    scrollY: window.scrollY, docH: document.documentElement.scrollHeight, winH: window.innerHeight,
    qaGrid: a && getComputedStyle(a).gridRowStart, quizGrid: q && getComputedStyle(q).gridRowStart});
})()"""

TRACE_JS = r"""(function () {
  if (window.__wbLog) return;
  window.__wbLog = [];
  function log(n) {
    var st = (new Error().stack || '').split('\n').slice(2, 5).map(function (x) { return x.trim(); }).join(' | ');
    window.__wbLog.push(Math.round(performance.now()) + ' ' + n + ' y=' + Math.round(window.scrollY) + ' ' + st);
  }
  ['scrollIntoView', 'scrollTo', 'scrollBy'].forEach(function (m) {
    var o = Element.prototype[m];
    if (o) Element.prototype[m] = function () { log('el.' + m + ' ' + (this.id || this.tagName)); return o.apply(this, arguments); };
  });
  var f = HTMLElement.prototype.focus;
  HTMLElement.prototype.focus = function () { log('focus ' + (this.id || this.tagName)); return f.apply(this, arguments); };
  var ws = window.scrollTo;
  window.scrollTo = function () { log('win.scrollTo'); return ws.apply(window, arguments); };
  var last = -1;
  window.addEventListener('scroll', function () {
    var y = Math.round(window.scrollY);
    if (Math.abs(y - last) > 40) { last = y; log('scroll'); }
  }, true);
  window.addEventListener('hashchange', function () { log('hash ' + location.hash); });
})()"""

TRACE_DUMP_JS = "JSON.stringify(window.__wbLog || [])"

CHAT_JS = """(function () {
  var u = document.querySelector('#wb-chat ul');
  if (!u) return 'none';
  var r = document.getElementById('wb-chat').getBoundingClientRect();
  return JSON.stringify({items: u.children.length, scrollTop: Math.round(u.scrollTop), scrollHeight: u.scrollHeight,
    clientHeight: u.clientHeight, chatBottom: Math.round(r.bottom), winH: window.innerHeight,
    overflowY: getComputedStyle(u).overflowY});
})()"""

LESSON_JS = """(function () {
  var q = document.getElementById('wb-quiz');
  return q ? q.className + ' | ' + (q.querySelector('.wb-q-head') || {}).textContent + ' | ' +
    q.querySelectorAll('.wb-lesson').length + ' lesson | ' + q.querySelectorAll('.wb-l-jp ruby').length + ' ruby' : 'none';
})()"""

HIT_JS = """(function () {
  function hit(sel) {
    var el = document.querySelector(sel);
    if (!el) return 'missing';
    var r = el.getBoundingClientRect(), x = r.left + Math.min(30, r.width / 2), y = r.top + r.height / 2;
    var top = document.elementFromPoint(x, y);
    return (top === el || el.contains(top)) ? 'ok' : ('covered by ' + (top ? (top.id || top.tagName + '.' + top.className) : 'nothing'));
  }
  return JSON.stringify({stream: hit('#wb-stream > .wb-title'), chat: hit('#wb-chat > .wb-title'), pat: hit('.wb-pat'),
    pe: getComputedStyle(document.querySelector('#wb-stream > .wb-title')).pointerEvents});
})()"""

TRY_JS = "(function(){try{%s;return 'ok';}catch(e){return 'ERR '+e.message+' | '+String(e.stack).slice(0,300);}})()"

DIAG_JS = """(function () {
  try {
    var before = Array.prototype.map.call(document.querySelectorAll('.wb-hearts-r'), function (h) { return h.style.animation; });
    var r = window.wbStream.debugPat(1);
    var after = Array.prototype.map.call(document.querySelectorAll('.wb-hearts-r'), function (h) { return h.style.animation; });
    return JSON.stringify({streams: document.querySelectorAll('#wb-stream').length, pats: document.querySelectorAll('.wb-pat').length,
      body: document.body.className, dp: typeof window.wbStream.debugPat, info: window.wbStream.debugInfo ? window.wbStream.debugInfo() : null,
      before: before, after: after, sprite: document.querySelector('.wb-kangel').style.backgroundImage});
  } catch (e) { return 'ERR ' + e.message; }
})()"""

PAT_JS = """(function () {
  var s = document.querySelector('.wb-kangel'), h = document.querySelector('.wb-hearts-r'),
      p = document.querySelector('.wb-pat'), last = document.querySelector('#wb-chat li:last-child .jp');
  return JSON.stringify({sprite: s ? s.style.backgroundImage.split('assets/').pop() : 'none',
    hearts: h ? h.style.animation : 'none', patVisible: p ? getComputedStyle(p).display : 'none',
    lastLine: last ? last.textContent : ''});
})()"""

DRAG_JS = """(function () {
  function drag(sel, dx, dy) {
    var t = document.querySelector(sel + ' > .wb-title'), r = t.getBoundingClientRect();
    var x = r.left + 20, y = r.top + 10, o = {bubbles: true, button: 0, pointerId: 7, isPrimary: true};
    t.dispatchEvent(new PointerEvent('pointerdown', Object.assign({clientX: x, clientY: y}, o)));
    t.dispatchEvent(new PointerEvent('pointermove', Object.assign({clientX: x + dx, clientY: y + dy}, o)));
    t.dispatchEvent(new PointerEvent('pointerup', Object.assign({clientX: x + dx, clientY: y + dy}, o)));
  }
  drag('#wb-stream', -900, 200);
  drag('#wb-chat', -1400, -200);
})()"""

POS_JS = """(function () {
  function box(id) { var r = document.getElementById(id).getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]; }
  return JSON.stringify({stream: box('wb-stream'), chat: box('wb-chat'), winW: innerWidth, winH: innerHeight,
    layout: window.wbLayout || null});
})()"""

SPRITE_JS = "(function(){var s=document.querySelector('.wb-kangel');return s?s.style.backgroundImage.split('assets/').pop():'none';})()"


def _dev_tour():
    if not os.path.exists(DEV_FLAG):
        return
    with open(DEV_FLAG, encoding="utf-8-sig") as fh:
        tour_deck = fh.read().strip()
    os.remove(DEV_FLAG)
    os.makedirs(DEV_DIR, exist_ok=True)

    def dump(name, web):
        def save(text):
            with open(os.path.join(DEV_DIR, f"{name}.html"), "w", encoding="utf-8") as fh:
                fh.write(text or "")
        web.evalWithCallback("document.documentElement.outerHTML", save)

    def mark(phase):
        with open(os.path.join(DEV_DIR, "phase.txt"), "w", encoding="utf-8") as fh:
            fh.write(phase)

    def go_overview():
        mw.col.decks.select(mw.col.decks.id_for_name(_config()["rename_default_deck_to"]) or 1)
        mw.moveToState("overview")

    def log_focus(tag):
        mw.reviewer.bottom.web.evalWithCallback(
            "(document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.ease : 'none')",
            lambda v: _dev_log(f"{tag}: focused ease {v}, verdict {json.dumps(_quiz['verdict'], ensure_ascii=False)}"))

    def probe(tag, web, js):
        web.evalWithCallback(js, lambda v: _dev_log(f"{tag}: {v}"))

    def type_answer(meaning, reading):
        mw.reviewer.web.eval(TYPE_JS % (json.dumps(meaning), json.dumps(reading)))

    steps = [
        (4000, lambda: mark("deckbrowser")),
        (8500, lambda: mw.web.eval("window.wbOpenStart && window.wbOpenStart();")),
        (9000, lambda: mark("startmenu")),
        (14500, lambda: mw.web.eval("document.body.click();")),
        (15000, go_overview),
        (18000, lambda: (mark("overview"), dump("overview", mw.web))),
        (24000, lambda: mw.moveToState("review")),
        (25500, lambda: mw.reviewer.web.eval(TRACE_JS)),
        (27000, lambda: (type_answer("moi", "watashi"), mark("typed"), probe("layout_typed", mw.reviewer.web, LAYOUT_JS))),
        (33000, lambda: mw.reviewer.web.eval("window.wbQuiz.submit(false);")),
        (35000, lambda: (mark("result_ok"), dump("result_ok", mw.reviewer.web), dump("result_ok_bottom", mw.reviewer.bottom.web))),
        (36000, lambda: (log_focus("ok"), probe("layout_ok", mw.reviewer.web, LAYOUT_JS),
                         _dev_log("voice: " + _media_file_filter("私_ワタシ━_0_NHK-2016.mp3")),
                         _dev_log("voice: " + _media_file_filter("JLPT_Tango_N5_0001.mp3")))),
        (41000, lambda: mw.reviewer._showQuestion()),
        (43000, lambda: type_answer("toi", "anata")),
        (44000, lambda: mw.reviewer.web.eval("window.wbQuiz.submit(false);")),
        (45500, lambda: (mark("result_ko"), probe("lesson_typed", mw.reviewer.web, LESSON_JS),
                         dump("result_learn_bottom", mw.reviewer.bottom.web))),
        (47000, lambda: log_focus("ko")),
        (49000, lambda: mw.reviewer._showQuestion()),
        (51000, lambda: mw.reviewer.web.eval("window.wbQuiz.submit(true);")),
        (52500, lambda: (mark("result_skip"), probe("lesson_skip", mw.reviewer.web, LESSON_JS))),
        (53500, lambda: log_focus("skip")),
        (54000, lambda: mw.reviewer._showQuestion()),
        (55000, lambda: mw.reviewer.web.eval("window.wbQuiz.submit(false);")),
        (55600, lambda: (mark("result_empty"), probe("lesson_empty", mw.reviewer.web, LESSON_JS), log_focus("empty"))),
        (56000, lambda: mw.reviewer.web.eval("window.wbStream.debugIdle(10);")),
        (57000, lambda: (mark("idle_kangel"), probe("idle_kangel", mw.reviewer.web, SPRITE_JS))),
        (60000, lambda: mw.reviewer.web.eval("window.wbStream.debugCheer(7);")),
        (61500, lambda: (mark("chat"), probe("chat", mw.reviewer.web, CHAT_JS))),
        (65000, lambda: _set_character("ame")),
        (66000, lambda: (mark("ame"), probe("trace", mw.reviewer.web, TRACE_DUMP_JS))),
        (68000, lambda: probe("hit", mw.reviewer.web, HIT_JS)),
        (71000, lambda: mw.reviewer.web.eval("window.wbStream.debugIdle(10);")),
        (72000, lambda: (mark("idle_ame"), probe("idle_ame", mw.reviewer.web, SPRITE_JS))),
        (77000, lambda: mw.reviewer.web.eval("window.wbStream.debugIdle(70);")),
        (78000, lambda: (mark("sleep_ame"), probe("sleep_ame", mw.reviewer.web, SPRITE_JS))),
        (79300, lambda: probe("diag", mw.reviewer.web, DIAG_JS)),
        (79800, lambda: mw.reviewer.web.eval("window.wbStream.debugPat(4);")),
        (80000, lambda: mark("pat_ame")),
        (81000, lambda: probe("drag_check", mw.reviewer.web,
                              "(function(){var b=" + POS_JS + ";" + DRAG_JS + ";return b+' => '+" + POS_JS + ";})()")),
        (81200, lambda: mark("moved")),
        (82400, lambda: mw.reviewer.web.eval(
            "document.querySelector('#wb-stream > .wb-title').dispatchEvent(new MouseEvent('dblclick', {bubbles: true}));"
            "document.querySelector('#wb-chat > .wb-title').dispatchEvent(new MouseEvent('dblclick', {bubbles: true}));")),
        (82800, lambda: probe("reset", mw.reviewer.web, POS_JS)),
        (83000, lambda: (_set_character("kangel"), mw.moveToState("deckBrowser"))),
        (86000, lambda: mw.web.eval("window.wbOpenStart && window.wbOpenStart();")),
        (86500, lambda: mark("startmenu2")),
        (90000, lambda: mw.web.eval("document.body.click();")),
        (91000, lambda: mark("done")),
    ]
    if tour_deck and tour_deck != "go":
        # Short tour of another deck (e.g. "JLPT Tango"): its card, a right answer,
        # "Je ne sais pas" and the lesson. Like the full tour, it never answers a card.
        def go_deck():
            mw.col.decks.select(mw.col.decks.id_for_name(tour_deck) or 1)
            mw.moveToState("review")

        def type_right():
            checks = _quiz["checks"] or {}
            meaning = _meaning_options(checks.get("meaning", ""))[:1]
            reading = _reading_options(checks.get("reading", ""))[:1]
            _dev_log(f"right answer: {meaning} {reading}")
            type_answer(meaning[0] if meaning else "", _romaji(reading[0]) if reading else "")

        card_js = ("(function(){var q=document.getElementById('qa'),w=document.querySelector('.wrap'),"
                   "s=document.querySelectorAll('#wb-quiz small');return JSON.stringify({qa:q&&Math.round("
                   "q.getBoundingClientRect().width),wrapBg:w&&getComputedStyle(w).backgroundColor,"
                   "body:getComputedStyle(document.body).display,hints:[].map.call(s,function(x){"
                   "return x.textContent}),fr:(document.querySelector('.ensentence')||{}).textContent||''});})()")
        steps = [
            (4000, lambda: mark("deckbrowser")),
            (6000, go_deck),
            (9000, lambda: (mark("tango_q"), probe("tango_q", mw.reviewer.web, card_js))),
            (12000, type_right),
            (12800, lambda: mark("tango_typed")),
            (15000, lambda: mw.reviewer.web.eval("window.wbQuiz.submit(false);")),
            (17000, lambda: (mark("tango_ok"), probe("tango_a", mw.reviewer.web, card_js), log_focus("tango_ok"),
                             dump("tango_a", mw.reviewer.web))),
            (20000, lambda: mw.reviewer.web.eval("window.scrollTo(0, document.body.scrollHeight);")),
            (20500, lambda: mark("tango_bottom")),
            (23000, lambda: mw.reviewer._showQuestion()),
            (25000, lambda: mw.reviewer.web.eval("window.wbQuiz.submit(true);")),
            (27000, lambda: (mark("tango_learn"), probe("tango_lesson", mw.reviewer.web, LESSON_JS),
                             _dev_log("voice: " + _media_file_filter("1_Chap1_Sec1.webm")))),
            (30000, lambda: mw.moveToState("deckBrowser")),
            (32000, lambda: mark("decks")),
            (34000, lambda: mark("done")),
        ]
    for delay, fn in steps:
        QTimer.singleShot(delay, fn)


# ── first run on a new PC: import the decks Installer.cmd left in user_files/setup ──

SETUP_DIR = os.path.join(ADDON_DIR, "user_files", "setup")


def _first_run():
    if mw.col is None:
        return
    try:
        from . import first_run
        if not first_run.pending(SETUP_DIR):
            return
        from aqt.operations import QueryOp
        from aqt.utils import showInfo, showWarning
    except Exception as exc:
        _dev_log(f"first run unavailable: {exc!r}")
        return

    def done(report):
        mw.moveToState("deckBrowser")
        showInfo(first_run.summary(report), title="べんきょう.exe")

    def failed(exc):
        showWarning("L'installation des paquets de cartes a échoué. Elle sera retentée au prochain "
                    f"lancement d'Anki.\n\n{exc}", title="べんきょう.exe")

    QueryOp(parent=mw, op=lambda col: first_run.run(col, SETUP_DIR), success=done).failure(failed) \
        .with_progress("Installation des paquets de cartes…").run_in_background()


def _on_profile_open():
    _rename_default_deck()
    _apply_window_chrome()
    QTimer.singleShot(0, _dev_tour)
    QTimer.singleShot(800, _first_run)


gui_hooks.profile_did_open.append(_on_profile_open)
gui_hooks.theme_did_change.append(lambda: QTimer.singleShot(0, _apply_window_chrome))
