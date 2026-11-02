"""Build the Windose Benkyou add-on assets from files already on this machine.

Sources (read only): textures and fonts exported from NEEDY GIRL OVERDOSE,
the Opera GX sound pack and one Chrome theme background made earlier.
Everything is written into <addon_dir>/web/assets, web/fonts and sounds.
Usage: python -I build_windose.py <raw> <preview> <gx_sound_dir> <chrome_dir> <addon_dir>
"""
import array
import os
import shutil
import sys
import wave

from PIL import Image

raw, preview, gx_sounds, chrome, addon = sys.argv[1:6]
assets = os.path.join(addon, "web", "assets")
fonts = os.path.join(addon, "web", "fonts")
sounds = os.path.join(addon, "sounds")
for d in (assets, fonts, sounds):
    os.makedirs(d, exist_ok=True)


def src(name):
    for base in (raw, preview):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(name)


def copy_png(name, out):
    Image.open(src(name)).convert("RGBA").save(os.path.join(assets, out), optimize=True)


# Windose desktop wallpaper: one 72 px period of the zigzag pattern.
Image.open(src("FHDbg.png")).convert("RGB").crop((896, 483, 968, 555)).save(
    os.path.join(assets, "wall_windose.png"), optimize=True)

# The Needy Streamer Overload Chrome theme background, as an optional wallpaper.
nso = os.path.join(chrome, "needy-streamer-overload-clair", "images", "ntp_background.png")
if os.path.exists(nso):
    im = Image.open(nso).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    im.save(os.path.join(assets, "wall_nso.jpg"), quality=88, optimize=True)

# Window frame and title bar pieces.
for name, out in [
    ("windowbase_active.png", "window.png"),
    ("windowbase_icon.png", "win_icon.png"),
    ("button_minimize.png", "b_min.png"),
    ("button_maximize.png", "b_max.png"),
    ("button_close.png", "b_close.png"),
    ("BaseButton.png", "btn.png"),
    ("BaseButtonHovered.png", "btn_hover.png"),
    ("BaseButtonPressed.png", "btn_down.png"),
    ("button_start.png", "start.png"),
    ("cursor.png", "cursor.png"),
    ("cursor_hand.png", "cursor_hand.png"),
    ("icon_status_follower.png", "st_follower.png"),
    ("icon_status_love.png", "st_love.png"),
    ("icon_status_stress.png", "st_stress.png"),
    ("icon_heart.png", "heart.png"),
    ("icon_pinkheart.png", "pinkheart.png"),
    ("bg_stream.png", "stream_bg.png"),
]:
    copy_png(name, out)

# KAngel's stream animations, one horizontal strip per animation.
ANIMS = {
    "idle": ["000", "001"],
    "eeto": ["000", "001"],
    "teach": ["000", "001"],
    "shobon": ["000", "001"],
    "kashikoma": ["000", "001", "002", "003", "004", "005", "006", "007"],
    "peace": ["000", "001", "002"],
    "pointing": ["000", "001", "003", "004", "005"],
    "smile": ["001", "002", "003", "004", "005", "006", "007"],
    "kawaiku": ["000", "001", "002"],
    "su_smile": ["000", "001"],
    "akaruku_superchat": ["000", "001", "002", "003"],
}
for anim, frames in ANIMS.items():
    imgs = [Image.open(src(f"stream_cho_{anim}_{f}.png")).convert("RGBA") for f in frames]
    w, h = imgs[0].size
    strip = Image.new("RGBA", (w * len(imgs), h), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        strip.paste(im, (i * w, 0))
    strip.save(os.path.join(assets, f"k_{anim}.png"), optimize=True)
    print(f"k_{anim}.png", len(imgs), "frames", strip.size)

# Start menu: the game's menu panel, its selection bar and desktop icons at half size.
menu_dir = sys.argv[6] if len(sys.argv) > 6 else None
if menu_dir:
    Image.open(os.path.join(menu_dir, "start_menu.png")).convert("RGBA").save(
        os.path.join(assets, "start_menu.png"), optimize=True)
    Image.open(os.path.join(menu_dir, "button_startmenu_selected.png")).convert("RGBA").save(
        os.path.join(assets, "menu_sel.png"), optimize=True)
    for name, out in [("asobu", "m_study"), ("folder_open2", "m_decks"), ("text", "m_add"),
                      ("egosearch", "m_browse"), ("internet", "m_sync"), ("neru", "m_quit"),
                      ("okusuri", "m_settings")]:
        im = Image.open(os.path.join(menu_dir, f"icon_desktop_{name}.png")).convert("RGBA")
        im.resize((32, 32), Image.BOX).save(os.path.join(assets, f"{out}.png"), optimize=True)

# Game fonts.
for name in ("PixelMplus10-Regular.ttf", "PixelMplus10-Bold.ttf"):
    shutil.copyfile(src(name), os.path.join(fonts, name))


# Sounds from the Opera GX pack, pre-mixed quieter so no volume control is needed.
def quiet_copy(name, gain=0.45):
    with wave.open(os.path.join(gx_sounds, name + ".wav")) as w:
        params = w.getparams()
        data = array.array("h", w.readframes(w.getnframes()))
    if params.sampwidth != 2:
        raise ValueError(name)
    peak = max(1, max(abs(v) for v in data))
    # Find where the sound really ends (last sample above 2% of peak).
    last = max((i for i, v in enumerate(data) if abs(v) > peak * 0.02), default=0)
    out = array.array("h", (int(v * gain) for v in data))
    with wave.open(os.path.join(sounds, name + ".wav"), "wb") as w:
        w.setparams(params)
        w.writeframes(out.tobytes())
    print(name, "audible", round(last / params.nchannels / params.framerate, 2), "s")


for name in ("status_up", "sippai", "piporo", "Tetehen", "result_start", "poko", "status_down", "kari"):
    quiet_copy(name)
print("done")


# ── characters: KAngel's extra animations and Ame's, one strip per animation ──
# Usage extension: argv[7] = folder with the idle exports, argv[8] = folder with Ame's exports.
if len(sys.argv) > 8:
    idle_dir, ame_dir = sys.argv[7], sys.argv[8]

    def frames_in(folder, prefix):
        names = sorted(n for n in os.listdir(folder)
                       if n.startswith(prefix) and n[len(prefix):-4].isdigit())
        return [os.path.join(folder, n) for n in names]

    def strip(paths, out):
        imgs = []
        for p in paths:
            im = Image.open(p).convert("RGBA")
            if im.size != (348, 227):
                im = im.resize((348, 227), Image.LANCZOS)
            imgs.append(im)
        sheet = Image.new("RGBA", (348 * len(imgs), 227), (0, 0, 0, 0))
        for i, im in enumerate(imgs):
            sheet.paste(im, (i * 348, 0))
        sheet.save(os.path.join(assets, out), optimize=True)
        print(out, len(imgs), "frames")

    for anim in ("ice", "tweet1", "tweet2", "balanceball", "game", "otaku", "kobiru", "su", "gaoo",
                 "pout", "sorrow_smile", "pray", "sleepy"):
        strip(frames_in(idle_dir, f"stream_cho_{anim}_"), f"k_{anim}.png")
    for anim in ("idle_normal", "talk", "idle", "positive", "negative", "smile", "idle_happy", "henoji",
                 "selfie", "idle_anxiety", "idle_iraira", "sleep"):
        strip(frames_in(ame_dir, f"stream_ame_{anim}_"), f"a_{anim}.png")
    for anim in ("handspinner", "nail", "headphone", "tv", "hair_drill", "hair_long", "hair_poney",
                 "hair_side", "egosearching", "game", "movie", "voice_training"):
        strip(frames_in(idle_dir, f"stream_ame_{anim}_"), f"a_{anim}.png")
    for name, out in (("icon_cho", "icon_kangel.png"), ("icon_ame", "icon_ame.png"),
                      ("icon_jine_ame", "jine_ame.png"), ("JINEBG", "jine_bg.png")):
        Image.open(os.path.join(ame_dir, name + ".png")).convert("RGBA").save(
            os.path.join(assets, out), optimize=True)
    print("characters done")
