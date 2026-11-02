"""KAngel and Ame speak the Kaishi 1.5k cards, with the owner's own GPT-SoVITS models (D:\\TTS).

Personal use only: the clips stay in the Windose Benkyou add-on's user_files folder,
never in collection.media, so nothing is synced or shared.

For every note, the word and the example sentence are spoken and saved where the
add-on looks for them:
  %APPDATA%/Anki2/addons21/windose_benkyou/user_files/voices/<character>/<id>.mp3
<id> comes from the card's original audio file name, so the add-on can play her
clip instead of the NHK / JLPT Tango recording. No clip means the original plays.

  * The word is spoken from its kana reading, with the pitch accent given by the
    NHK file name or the card's Pitch Accent field.
  * The sentence is checked against the card's furigana; when OpenJTalk would read
    a kanji differently, the sentence is spoken from its furigana.
  * Each clip is checked: length for its number of moras, and a local Whisper
    transcription read back in kana. A clip that fails three seeds is not written,
    so the original recording keeps playing for that card.
  * The job stops at once if the live voice app runs (no GPU work next to it).
    Run it again to resume: finished clips are kept.

Run inside D:\\TTS\\GPT-SoVITS\\venv, at low priority through run-low.ps1:
  python -s sovits_voicegen.py build [--chars kangel,ame] [--limit N] [--first N]
  python -s sovits_voicegen.py test <out_dir> [--limit N]
"""
import difflib
import hashlib
import html
import json
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voicegen as vg  # noqa: E402  (note loading, furigana and pitch helpers)

G = r"D:\TTS\GPT-SoVITS"
PRE = "GPT_SoVITS/pretrained_models"
VOICES_JSON = r"D:\TTS\tools\scripts\tts_page\voices.json"
WHISPER = r"D:\TTS\tools\model-faster-whisper-large-v3"
VOICES = vg.VOICES

# Emotion of the reference clips, per kind of clip.
EMOTION = {"kangel": {"word": "neutral", "sentence": "neutral"},
           "ame": {"word": "neutral", "sentence": "neutral"}}
SPEED = {"word": 0.95, "sentence": 1.0}
TRIES = 3
SHORT_TRIES = 5      # words of 1 to 3 moras: Whisper hears them badly on their own
SHORT = 3
PASS = {"word": 0.8, "sentence": 0.82}   # reading similarity that accepts a clip at once
KEEP = {"word": 0.67, "sentence": 0.7}   # best of the tries is still kept above this
SR_OUT = 32000

LIVE_MARKERS = ("realtime_gui.py", "\\tools\\voix\\", "/tools/voix/")


# ── the live voice app owns the GPU ──────────────────────────────────────────

def live_voice_running():
    import psutil
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            if "python" not in (p.info["name"] or "").lower():
                continue
            cmd = " ".join(p.info["cmdline"] or [])
            if any(m.lower() in cmd.lower() for m in LIVE_MARKERS):
                return True
        except Exception:
            continue
    return False


# ── forced pitch accent for a single word ────────────────────────────────────

FORCE = {}


def install_accent_patch():
    """OpenJTalk gives the word's accent to GPT-SoVITS as [ and ] marks: use the card's."""
    import pyopenjtalk
    if getattr(pyopenjtalk, "_wb_patched", False):
        return
    original = pyopenjtalk.run_frontend

    def run_frontend(text, *args, **kwargs):
        feats = original(text, *args, **kwargs)
        acc = FORCE.get(text)
        if acc is None or not feats:
            return feats
        feats = [dict(f) for f in feats]
        feats[0]["acc"] = acc
        feats[0]["chain_flag"] = -1
        for f in feats[1:]:
            f["chain_flag"] = 1  # one accent phrase for the whole word
        return feats

    pyopenjtalk.run_frontend = run_frontend
    pyopenjtalk._wb_patched = True


SMALL = set("ァィゥェォャュョヮぁぃぅぇぉゃゅょゎ")


def moras(kana):
    return sum(1 for ch in kana if ch not in SMALL and ("ぁ" <= ch <= "ゖ" or "ァ" <= ch <= "ヶ" or ch == "ー"))


def word_accent(audio_name, pitch_html, reading):
    """The accent number (0 = flat) from the NHK file name or the Pitch Accent field."""
    m = vg.NHK.match(os.path.splitext(audio_name or "")[0])
    marked = m.group("kana").replace("━", "") if m else vg.pitch_marks(pitch_html)
    marked = re.sub("([カキクケコ])゚", lambda x: chr(ord(x.group(1)) + 1), marked)
    if not marked or marked.count("＼") > 1:
        return None, None
    if reading and vg.sound_key(marked.replace("＼", "")) != vg.sound_key(reading):
        return None, None
    acc = moras(marked.split("＼")[0]) if "＼" in marked else 0
    return acc, ("nhk" if m else "pitch")


# ── texts to speak ───────────────────────────────────────────────────────────

def kana_reading(text):
    import pyopenjtalk
    return pyopenjtalk.g2p(text, kana=True)


def word_text(note):
    reading = vg.first_reading(note.get("Word Reading"))
    word = vg.plain(note.get("Word"))
    return (reading or word), reading or vg.hira(kana_reading(word)), word


def furigana_readings(field_html):
    """Every kana reading of an Anki furigana word field, alternatives expanded.

    JLPT Tango writes 開[あ<br>ひら]く, 吃驚[きっきょう、びっくり], 抱[いだ]く/ 抱[だ]く,
    注意[ちゅうい]＜する＞ or 御洒落[おしゃれ](な/する): the readings are あく and ひらく, ...
    """
    text = re.sub(r"<br\s*/?>", "|", field_html or "", flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).replace("\xa0", " ")
    text = re.sub(r"\([^)]*\)|（[^）]*）|＜[^＞]*＞|<[^>]*>", "", text)
    out = []
    for variant in re.split(r"\s*[/／・]\s*(?![^\[]*\])", text):
        pieces = [[""]]
        pos = 0
        for m in vg.FURIGANA.finditer(variant):
            pieces.append([variant[pos:m.start()]])
            pieces.append([a.strip() for a in re.split(r"[|、,，;]", m.group(2)) if a.strip()] or [""])
            pos = m.end()
        pieces.append([variant[pos:]])
        combos = [""]
        for alts in pieces:
            combos = [c + a for c in combos for a in alts][:6]
        for c in combos:
            h = vg.hira(c)
            if h and h not in out:
                out.append(h)
    return out


TANGO_JSON = os.path.join(HERE, "..", "tango", "work", "tango_notes.json")


def tango_notes():
    """The JLPT Tango N4/N3/N2 notes, under the Kaishi field names this script speaks."""
    with open(TANGO_JSON, encoding="utf-8") as fh:
        records = json.load(fh)
    notes = []
    for r in records:
        readings = furigana_readings(r.get("VocabFurigana"))
        note = {"Word": re.sub(r"\[\d+\]", "", vg.plain(r.get("VocabKanji"))).strip(),
                "Word Reading": readings[0] if readings else "",
                "Sentence": r.get("SentKanji") or "", "Sentence Furigana": r.get("SentFurigana") or "",
                "Word Audio": r.get("VocabAudio") or "", "Sentence Audio": r.get("SentAudio") or "",
                "Pitch Accent": "", "_deck": r.get("deck")}
        pitch = (r.get("VocabPitchNum") or "").strip()
        if re.fullmatch(r"\d{1,2}", pitch) and readings and int(pitch) <= moras(readings[0]):
            note["_acc"] = int(pitch)
        notes.append(note)
    return notes


def sentence_text(note):
    text = vg.no_labels(vg.plain(note.get("Sentence")))
    want = vg.no_labels(vg.furigana_reading(note.get("Sentence Furigana"))) if note.get("Sentence Furigana") else ""
    if want and vg.sound_key(kana_reading(text)) != vg.sound_key(want):
        return want, want, "furigana"
    return text, want or kana_reading(text), "kanji"


# ── models ───────────────────────────────────────────────────────────────────

class Voices:
    def __init__(self):
        os.chdir(G)
        sys.path[:0] = [G, os.path.join(G, "GPT_SoVITS")]
        with open(VOICES_JSON, encoding="utf-8") as fh:
            self.conf = json.load(fh)
        self.tts = None
        self.char = None
        self.asr = None

    def load(self, char):
        c = self.conf["chars"][char]
        if self.tts is None:
            from TTS_infer_pack.TTS import TTS, TTS_Config
            cfg = TTS_Config({"custom": {
                "device": "cuda", "is_half": True, "version": self.conf["version"],
                "t2s_weights_path": c["gpt"], "vits_weights_path": c["sovits"],
                "bert_base_path": f"{PRE}/chinese-roberta-wwm-ext-large",
                "cnhuhbert_base_path": f"{PRE}/chinese-hubert-base"}})
            self.tts = TTS(cfg)
            install_accent_patch()
        elif self.char != char:
            self.tts.init_vits_weights(c["sovits"])
            self.tts.init_t2s_weights(c["gpt"])
        self.char = char

    def speak(self, text, emotion, speed, seed):
        refs = self.conf["chars"][self.char]["refs"][emotion]
        parts, rate = [], SR_OUT
        for sr, chunk in self.tts.run({
                "text": text, "text_lang": "all_ja", "ref_audio_path": refs[0]["path"],
                "aux_ref_audio_paths": [r["path"] for r in refs[1:3]], "prompt_text": refs[0]["text"],
                "prompt_lang": "ja", "top_k": 15, "top_p": 1.0, "temperature": 1.0,
                "text_split_method": "cut3", "fragment_interval": 0.15, "batch_size": 1,
                "speed_factor": speed, "seed": seed, "parallel_infer": True,
                "repetition_penalty": 1.35, "return_fragment": False}):
            rate = sr
            parts.append(np.asarray(chunk))
        y = np.concatenate(parts).astype(np.float32) if parts else np.zeros(1, np.float32)
        return (y / 32768.0 if np.abs(y).max() > 1.5 else y), rate

    def hear(self, y, sr, hint=None):
        if self.asr is None:
            from faster_whisper import WhisperModel
            self.asr = WhisperModel(WHISPER, device="cuda", compute_type="float16")
        if sr != 16000:
            idx = np.arange(0, len(y), sr / 16000.0)
            y = np.interp(idx, np.arange(len(y)), y).astype(np.float32)
        segs, _ = self.asr.transcribe(y, language="ja", beam_size=5, vad_filter=False, initial_prompt=hint,
                                      condition_on_previous_text=False, without_timestamps=True)
        return "".join(s.text for s in segs).strip()


# ── checks ───────────────────────────────────────────────────────────────────

def trim(y, sr):
    """Cut the silence around the speech; return the clip with short, even padding."""
    if not len(y):
        return y, 0.0
    frame = int(sr * 0.01)
    n = len(y) // frame
    if n == 0:
        return y, 0.0
    rms = np.sqrt(np.mean(y[:n * frame].reshape(n, frame) ** 2, axis=1))
    loud = np.where(rms > max(0.01, rms.max() * 0.05))[0]
    if not len(loud):
        return y, 0.0
    a, b = max(0, loud[0] - 3) * frame, min(n, loud[-1] + 6) * frame
    speech = y[a:b]
    pad = lambda s: np.zeros(int(sr * s), np.float32)  # noqa: E731
    return np.concatenate([pad(0.12), speech, pad(0.22)]), len(speech) / sr


def length_ok(kind, seconds, m):
    if kind == "word":
        return 0.06 * m + 0.12 <= seconds <= 0.32 * m + 0.9
    return 0.05 * m <= seconds <= 0.2 * m + 1.5


PUNCT = re.compile(r"[\s、。,.!?！？「」『』…・〜~ー()（）]")


def score(heard, want_kana, written):
    if not heard:
        return 0.0
    clean = PUNCT.sub("", heard)
    if any(clean and clean == PUNCT.sub("", w) for w in written if w):
        return 1.0
    a, b = vg.sound_key(kana_reading(heard)), vg.sound_key(want_kana)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def normalise(y):
    peak = float(np.abs(y).max()) if len(y) else 0.0
    return y * (0.89 / peak) if peak > 0 else y


def write_mp3(path, y, sr):
    import soundfile as sf
    tmp = path + ".part"
    sf.write(tmp, y, sr, format="MP3", subtype="MPEG_LAYER_III")
    os.replace(tmp, path)


def seed_for(name, attempt):
    return (int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16) + 7919 * attempt) % (2 ** 31)


def make_clip(v, kind, note, audio_name):
    """Best of up to TRIES seeds. Returns (audio, sr, info) or (None, None, info)."""
    if kind == "word":
        text, want, written_word = word_text(note)
        if "_acc" in note:  # JLPT Tango: the accent number written on the card
            acc, how = note["_acc"], "pitchnum"
        else:
            acc, how = word_accent(audio_name, note.get("Pitch Accent"), vg.hira(text))
        FORCE.clear()
        if acc is not None:
            FORCE[text] = acc
        written = [written_word, text, vg.hira(text)]
        say = text + "。"
    else:
        say, want, how = sentence_text(note)
        written = [vg.plain(note.get("Sentence")), say]
        acc = None
    m = max(1, moras(vg.hira(want)))
    short = kind == "word" and m <= SHORT
    best, hinted = None, None
    try:
        for attempt in range(SHORT_TRIES if short else TRIES):
            speed = SPEED[kind] - (0.05 if short and attempt % 2 else 0.0)
            y, sr = v.speak(say, EMOTION[v.char][kind], speed, seed_for(audio_name, attempt))
            y, seconds = trim(y, sr)
            ok_len = length_ok(kind, seconds, m)
            heard = v.hear(y, sr) if ok_len else ""
            s = score(heard, want, written) if ok_len else 0.0
            info = {"how": how or "reading", "acc": acc, "seconds": round(seconds, 2), "score": round(s, 2),
                    "try": attempt + 1, "heard": heard}
            if best is None or s > best[2]["score"]:
                best = (y, sr, info)
            if s >= PASS[kind]:
                break
            if short and ok_len:
                # Told which word to expect, Whisper still refuses a wrong or slurred take.
                heard2 = v.hear(y, sr, hint=f"{written[0]}、{want}。")
                s2 = score(heard2, want, written)
                if s2 >= PASS[kind] and (hinted is None or s > hinted[2]["score"]):
                    hinted = (y, sr, dict(info, hint_heard=heard2, hint_score=round(s2, 2)))
    finally:
        FORCE.clear()
    if best and best[2]["score"] >= KEEP[kind]:
        return best
    if hinted:
        return hinted
    return None, None, (best[2] if best else {"how": how, "score": 0.0})


# ── the job ──────────────────────────────────────────────────────────────────

def clips_of(note):
    for kind, field in (("word", "Word Audio"), ("sentence", "Sentence Audio")):
        name = vg.sound_name(note.get(field))
        if name:
            yield kind, name


def build(chars, limit=None, first=None, out_root=VOICES, verbose=False, source="kaishi"):
    notes = tango_notes() if source == "tango" else vg.kaishi_notes()
    if limit:
        notes = notes[:limit]
    v = Voices()
    if source == "tango":
        # Deck by deck (N4, then N3, then N2), both voices for each before the next.
        bounds = [i for i in range(1, len(notes)) if notes[i]["_deck"] != notes[i - 1]["_deck"]]
        edges = [0] + bounds + [len(notes)]
        plan = [(c, lo, hi) for lo, hi in zip(edges, edges[1:]) for c in chars]
    else:
        # The first cards get both voices early, then the rest one character at a time.
        head = first if first is not None else min(100, len(notes))
        plan = [(c, 0, head) for c in chars] + [(c, head, len(notes)) for c in chars if head < len(notes)]
    suffix = "" if source == "kaishi" else "_" + source
    stats = {c: {"made": 0, "kept": 0, "skipped": 0, "retried": 0, "furigana": 0, "nhk": 0, "pitch": 0,
                 "pitchnum": 0} for c in chars}
    start = time.time()
    for char, lo, hi in plan:
        out_dir = os.path.join(out_root, char)
        os.makedirs(out_dir, exist_ok=True)
        todo, seen = [], set()
        for i in range(lo, hi):
            for kind, name in clips_of(notes[i]):
                if name not in seen and not os.path.exists(os.path.join(out_dir, vg.clip_id(name) + ".mp3")):
                    todo.append((i, kind, name))
                seen.add(name)  # a few notes share the same example sentence
        st = stats[char]
        st["kept"] += sum(1 for i in range(lo, hi) for _ in clips_of(notes[i])) - len(todo)
        if not todo:
            continue
        if live_voice_running():
            print("STOP: the live voice app is running; run again later to resume.", flush=True)
            return 3
        v.load(char)
        print(f"{char}: notes {lo + 1}-{hi}, {len(todo)} clips to make", flush=True)
        report = open(os.path.join(out_dir, f"_report{suffix}.txt"), "a", encoding="utf-8")
        for n, (i, kind, name) in enumerate(todo, 1):
            if n % 20 == 0 and live_voice_running():
                print("STOP: the live voice app started; run again later to resume.", flush=True)
                report.close()
                return 3
            path = os.path.join(out_dir, vg.clip_id(name) + ".mp3")
            try:
                y, sr, info = make_clip(v, kind, notes[i], name)
            except Exception as exc:
                y, info = None, {"error": repr(exc)[:200]}
            if y is not None:
                write_mp3(path, normalise(y), sr)
                st["made"] += 1
                st["retried"] += info["try"] > 1
                st["hinted"] = st.get("hinted", 0) + ("hint_score" in info)
                st["furigana"] += info.get("how") == "furigana"
                st["nhk"] += info.get("how") == "nhk"
                st["pitch"] += info.get("how") == "pitch"
                st["pitchnum"] += info.get("how") == "pitchnum"
            else:
                st["skipped"] += 1
            report.write(json.dumps({"note": i + 1, "kind": kind, "audio": name, "written": y is not None,
                                     **info}, ensure_ascii=False) + "\n")
            if verbose:
                print(i + 1, kind, "written" if y is not None else "SKIPPED", info, flush=True)
            if n % 50 == 0 or n == len(todo):
                el = time.time() - start
                print(f"{char}: {n}/{len(todo)} clips ({lo + 1}-{hi}), {st}, {el / 60:.1f} min", flush=True)
                report.flush()
        report.close()
        with open(os.path.join(out_dir, f"_voice{suffix}.json"), "w", encoding="utf-8") as fh:
            json.dump({"engine": "GPT-SoVITS v2ProPlus (local, owner's models)", "character": char,
                       "voice": os.path.basename(v.conf["chars"][char]["sovits"]),
                       "source": source, "notes": len(notes), "stats": st}, fh)
    print("done", json.dumps(stats), f"{(time.time() - start) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d  # noqa: E731
    lim = int(opt("--limit")) if opt("--limit") else None
    src = opt("--source", "kaishi")
    if args[0] == "build":
        chars = opt("--chars", "kangel,ame").split(",")
        fst = int(opt("--first")) if opt("--first") else None
        sys.exit(build(chars, lim, fst, source=src))
    elif args[0] == "test":
        sys.exit(build(opt("--chars", "kangel,ame").split(","), lim or 4, None, out_root=args[1], verbose=True,
                       source=src))
    elif args[0] == "readings":  # dry check of the Tango readings and accents, no GPU
        ns = tango_notes()
        print("notes", len(ns), "no reading", sum(1 for n in ns if not n["Word Reading"]),
              "accent", sum(1 for n in ns if "_acc" in n))
        for n in ns[:int(opt("--show", "0"))]:
            print(n["Word"], n["Word Reading"], n.get("_acc"))
