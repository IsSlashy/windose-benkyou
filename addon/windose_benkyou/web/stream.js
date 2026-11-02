// Windose Benkyou: the stream window beside the card, with KAngel or Ame.
// - She reacts to each card with her own animations from the game.
// - When nothing happens she picks an activity (ice cream, hand spinner...),
//   chosen by mood, time of day and how long you have been still, never one
//   of the last three again. Any mouse move or key press brings her back to
//   her attentive pose, reading along with you.
// - The talk window shows what she says, in Japanese with the French meaning.
//   It scrolls like a live chat: new lines arrive at the bottom and push the
//   older ones up; you can scroll back with the wheel. While you study she
//   drops an encouragement every half minute to a minute.
// - The ⇄ button in the title bar switches between KAngel and Ame.
// Onigiri's review header lives in a shadow root that page CSS cannot reach,
// so it is restyled from here.
(function () {
  if (window.wbStream) return;

  var BASE = ((document.currentScript && document.currentScript.src) || "").replace(/stream\.js.*$/, "");
  var A = BASE + "assets/";

  // anim: [frames, seconds per loop]
  var CHARS = {
    kangel: {
      name: "KAngel",
      file: "k_",
      title: "LIVE ♡ 配信中",
      talkTitle: "KAngel ♡ トーク",
      avatar: "icon_kangel.png",
      other: "Ame",
      anim: {
        idle: [2, 1.6], eeto: [2, 1.0], teach: [2, 0.7], shobon: [2, 0.9], kashikoma: [8, 1.3],
        peace: [3, 0.6], pointing: [5, 0.8], smile: [7, 1.1], kawaiku: [3, 0.6], su_smile: [2, 0.8],
        akaruku_superchat: [4, 0.8], ice: [6, 1.2], tweet1: [3, 0.9], tweet2: [3, 0.9],
        balanceball: [11, 1.6], game: [5, 0.8], otaku: [7, 1.2], kobiru: [4, 0.8], su: [3, 0.7],
        gaoo: [2, 0.6], pout: [2, 0.9], sorrow_smile: [3, 0.9], pray: [5, 1.0], sleepy: [10, 2.0]
      },
      question: "eeto", answer: "teach", start: "kashikoma", milestone: "akaruku_superchat",
      yay: ["peace", "pointing", "smile", "kawaiku", "su_smile"], oops: ["shobon", "pout"],
      learn: ["pointing", "kawaiku"],
      idle: {
        neutral: ["ice", "tweet1", "tweet2", "balanceball", "game", "otaku"],
        happy: ["kobiru", "su", "gaoo", "smile"],
        down: ["pout", "sorrow_smile", "pray"],
        sleepy: ["sleepy"]
      },
      lines: {
        start: [["はーい、超てんちゃんだよ！にほんご配信はじめるよ〜", "c'est KAngel ! le live de japonais commence !"]],
        yay: [["せいかい！えらすぎ！", "bonne réponse ! trop fort !"], ["天才じゃん！", "t'es un génie !"],
              ["その調子その調子！", "continue comme ça !"], ["かんぺき〜！", "parfait !"],
              ["てんちゃんもびっくり！", "même KAngel est épatée !"], ["やるじゃん！", "pas mal du tout !"]],
        oops: [["ドンマイ！", "pas grave !"], ["つぎはいけるって！", "la prochaine, tu l'as !"],
               ["てんちゃんがついてるよ", "KAngel est avec toi"], ["もう一回おぼえよ！", "on la réapprend !"],
               ["まちがえるのも配信のうち！", "se tromper, ça fait partie du live !"]],
        milestone: {
          10: ["10枚！ウォームアップ完了！", "10 cartes ! échauffement terminé !"],
          25: ["25枚！ノってきたね！", "25 cartes ! ça s'emballe !"],
          50: ["50枚！？神回じゃん！", "50 cartes ?! live légendaire !"],
          100: ["100枚！！伝説の配信！", "100 cartes !! live mythique !"],
          150: ["150枚！もう止まらない！", "150 cartes ! plus rien ne t'arrête !"],
          200: ["200枚！！殿堂入り！", "200 cartes !! au panthéon !"],
          300: ["300枚！？伝説の伝説！", "300 cartes ?! la légende des légendes !"]
        },
        activity: {
          ice: ["アイスうま〜", "cette glace est trop bonne"],
          tweet1: ["ちょっとつぶやいとこ", "je poste un petit tweet"],
          tweet2: ["いまの配信、ツイートしよ", "je tweete le live"],
          balanceball: ["バランスボールで体幹きたえ中", "je muscle mes abdos sur le ballon"],
          game: ["ちょっとだけゲームしよ", "juste une petite partie"],
          otaku: ["みんな見てる〜？", "vous me regardez ?"],
          kobiru: ["今日のキミ、ノってるね", "t'es en forme aujourd'hui"],
          su: ["ふふっ", "hihi"],
          gaoo: ["がおー！", "graou !"],
          pout: ["むー", "boude"],
          sorrow_smile: ["だいじょうぶ、だいじょうぶ", "ça va aller, ça va aller"],
          pray: ["つぎはせいかいしますように…", "pourvu que la prochaine soit bonne…"],
          sleepy: ["ふぁ…ねむくなってきた", "ah… je commence à avoir sommeil"]
        },
        wake: [["はっ！起きてるよ！", "hein ! je dormais pas !"]],
        hello: [["てんちゃんにチェンジ！", "on passe à KAngel !"]],
        cheer: [["いいペースだよ！", "bon rythme !"], ["がんばってるキミ、さいこう！", "tu bosses dur, t'es au top !"],
                ["にほんご、どんどんうまくなってる！", "ton japonais progresse à vue d'œil !"],
                ["その調子でいこ〜！", "continue comme ça !"], ["てんちゃん、ずっと応援してるよ", "KAngel t'encourage, toujours"],
                ["まちがえても大丈夫、それが勉強！", "se tromper, c'est ça apprendre !"],
                ["ちょっとずつで、いいんだよ", "petit à petit, c'est très bien"],
                ["きょうのキミ、かっこいい！", "t'assures aujourd'hui !"]],
        minutes: ["もう{m}分も配信してる！えらい！", "déjà {m} minutes de live ! bravo !"],
        near: ["あと{k}枚で{n}枚！", "plus que {k} {cartes} avant {n} !"],
        streak: ["{s}連続せいかい！すごっ！", "{s} bonnes d'affilée ! trop fort !"]
      }
    },
    ame: {
      name: "Ame",
      file: "a_",
      title: "Ame ♡ おへや",
      talkTitle: "JINE ♡ Ame",
      avatar: "jine_ame.png",
      other: "KAngel",
      anim: {
        idle_normal: [12, 2.4], talk: [5, 0.8], idle: [2, 1.6], positive: [13, 1.6], negative: [14, 1.8],
        smile: [3, 0.8], idle_happy: [9, 1.6], henoji: [2, 0.9], selfie: [6, 1.2], idle_anxiety: [8, 1.6],
        idle_iraira: [6, 1.2], sleep: [9, 2.2], handspinner: [11, 1.1], nail: [5, 1.0], headphone: [3, 0.9],
        tv: [7, 1.2], hair_drill: [2, 1.0], hair_long: [2, 1.0], hair_poney: [2, 1.0], hair_side: [2, 1.0],
        egosearching: [5, 1.0], game: [5, 0.8], movie: [5, 1.0], voice_training: [8, 1.2]
      },
      question: "idle_normal", answer: "talk", start: "smile", milestone: "selfie",
      yay: ["positive", "smile", "idle_happy"], oops: ["negative", "henoji"],
      learn: ["smile", "talk"],
      idle: {
        neutral: ["handspinner", "nail", "headphone", "tv", "hair_drill", "hair_long", "hair_poney",
                  "hair_side", "egosearching", "game", "movie"],
        happy: ["idle_happy", "selfie", "smile", "voice_training"],
        down: ["idle_anxiety", "idle_iraira", "henoji"],
        sleepy: ["sleep"]
      },
      pat: {
        first: [["えへへ…", "héhé…"], ["なでなで、すき", "les caresses sur la tête, j'adore"],
                ["くすぐったいよ", "ça chatouille"], ["…ん。うれしい", "…mm. ça me fait plaisir"],
                ["ほめられてる？", "c'est pour me féliciter ?"], ["あめ、いいこ？", "Ame est sage ?"]],
        more: [["もっとして", "encore"], ["まだやめないで", "t'arrête pas"],
               ["ずっとこうしてたい…", "je voudrais rester comme ça…"]],
        enough: [["…べんきょうもしなよ？", "…et tes révisions alors ?"], ["はい、おしまい。つぎのカード", "allez, fini. carte suivante"]]
      },
      lines: {
        start: [["きょうもべんきょう？えらいじゃん", "encore des révisions aujourd'hui ? respect"]],
        yay: [["やるじゃん", "pas mal"], ["えらいえらい", "c'est bien, c'est bien"], ["すご。てんさい？", "waouh. un génie ?"],
              ["ほめてあげる", "je te félicite"], ["いいかんじ", "ça roule"], ["あめもうれしい", "ça me fait plaisir aussi"]],
        oops: [["どんまい", "pas grave"], ["あめもそれわかんない", "moi non plus je savais pas"],
               ["まあいっか、つぎ", "bon, tant pis, la suivante"], ["いっしょにおぼえよ", "on l'apprend ensemble"],
               ["ちょっとやすむ？", "on fait une pause ?"]],
        milestone: {
          10: ["10まい。けっこうやるじゃん", "10 cartes. pas mal du tout"],
          25: ["25まい…がんばりすぎじゃない？", "25 cartes… tu forces pas un peu ?"],
          50: ["50まい！じどりしとこ", "50 cartes ! je prends un selfie pour fêter ça"],
          100: ["100まい！？ほんとにすごい", "100 cartes ?! franchement impressionnant"],
          150: ["150まい…あめよりがんばってる", "150 cartes… tu bosses plus que moi"],
          200: ["200まい！！じまんしていいよ", "200 cartes !! tu peux t'en vanter"],
          300: ["300まい！？ちょっとこわい", "300 cartes ?! ça fait un peu peur"]
        },
        activity: {
          handspinner: ["ハンドスピナーくるくる…", "le hand spinner tourne, tourne…"],
          nail: ["ネイルかわいくない？", "elles sont pas mignonnes, mes ongles ?"],
          headphone: ["おんがくきいてる", "j'écoute de la musique"],
          tv: ["テレビつけとこ", "j'allume la télé"],
          hair_drill: ["かみがた、かえてみた", "j'ai changé de coiffure"],
          hair_long: ["かみ、おろしてみた", "cheveux détachés, pour voir"],
          hair_poney: ["ポニーテールどう？", "et la queue de cheval ?"],
          hair_side: ["サイドテールにしてみた", "une couette sur le côté"],
          egosearching: ["エゴサしよ…", "je cherche mon nom en ligne…"],
          game: ["ちょっとゲーム", "une petite partie"],
          movie: ["えいがみよ", "je regarde un film"],
          voice_training: ["ボイトレちゅう", "je travaille ma voix"],
          idle_happy: ["きょうはきぶんいい", "je suis de bonne humeur aujourd'hui"],
          selfie: ["じどりしとこ", "petit selfie"],
          idle_anxiety: ["…だいじょうぶかな", "…ça va aller, tu crois ?"],
          idle_iraira: ["むずかしいね、これ", "elle est dure, celle-là"],
          henoji: ["むぅ", "boude"],
          sleep: ["ねむ…", "j'ai sommeil…"]
        },
        wake: [["…ねてないよ", "…je dormais pas"]],
        hello: [["あめだよ。いっしょにべんきょうしよ", "c'est Ame. on étudie ensemble"]],
        cheer: [["がんばってるね", "tu bosses bien"], ["いいかんじ", "ça avance bien"], ["むりしないでね", "force pas trop, hein"],
                ["あめもいっしょにいるよ", "je suis là avec toi"], ["すこしずつでいいよ", "petit à petit, c'est bien"],
                ["きょうもえらい", "t'es au top aujourd'hui"], ["まちがえてもいいんだよ", "c'est ok de se tromper"],
                ["あめ、ちゃんとみてるよ", "je te regarde faire, hein"]],
        minutes: ["もう{m}ぷん。がんばってるね", "déjà {m} minutes. tu bosses bien"],
        near: ["あと{k}まいで{n}まい", "encore {k} et ça fait {n}"],
        streak: ["{s}れんぞく。やるじゃん", "{s} d'affilée. pas mal"]
      }
    }
  };

  var MILESTONES = [10, 25, 50, 100, 150, 200, 300];
  var MOOD_WEIGHT = 0.45;        // chance to pick from the mood pool rather than neutral
  var FIRST_IDLE = [7, 12];      // seconds of stillness before the first activity
  var NEXT_IDLE = [10, 20];      // seconds between activities
  var SLEEP_AFTER = 60;          // seconds of stillness before she falls asleep
  var LATE_SLEEP = 0.35;         // chance of dozing off instead, after 23:00
  var HOLD = 900;                // ms a one-shot reaction stays on its last frame
  var CHEER_EVERY = [30, 60];    // seconds between two encouragements while you study
  var CHEER_GAP = 12;            // never right after another line
  var CHAT_KEEP = 80;            // lines kept in the chat history
  var MINUTE_MARKS = [5, 10, 15, 20, 30, 45, 60, 90];

  var SHADOW_CSS = [
    "#onigiri-reviewer-header a.onigiri-reviewer-button:not(#wb-a):not(#wb-b), #onigiri-reviewer-header button:not(#wb-a):not(#wb-b) {",
    "  font-family: 'WB Pixel', monospace !important; font-size: 20px !important; color: #4d23cf !important;",
    "  background: transparent !important; border-style: solid !important; border-width: 4px !important;",
    "  border-image: url('" + A + "btn.png') 4 fill / 4px round !important;",
    "  border-radius: 0 !important; box-shadow: none !important; backdrop-filter: none !important; }",
    "#onigiri-reviewer-header a.onigiri-reviewer-button:not(#wb-a):not(#wb-b):hover { border-image-source: url('" + A + "btn_hover.png') !important; }",
    "#onigiri-reviewer-header a.onigiri-reviewer-button:not(#wb-a):not(#wb-b):active { border-image-source: url('" + A + "btn_down.png') !important; }",
    ".onigiri-reviewer-progress:not(#wb-a):not(#wb-b) { font-family: 'WB Pixel', monospace !important; font-size: 20px !important;",
    "  color: #4d23cf !important; background: #fff8ff !important; border-radius: 0 !important;",
    "  border: 2px solid #4d23cf !important; box-shadow: 4px 4px 0 rgba(77, 35, 207, 0.5) !important; backdrop-filter: none !important; }",
    ".onigiri-reviewer-progress .orp-text:not(#wb-a):not(#wb-b) { color: #4d23cf !important; font-family: 'WB Pixel', monospace !important; }",
    ".onigiri-reviewer-progress .orp-track:not(#wb-a):not(#wb-b) { background: #fff8ff !important; border: 2px solid #4d23cf !important; border-radius: 0 !important; }",
    ".onigiri-reviewer-progress .orp-fill:not(#wb-a):not(#wb-b) { background: repeating-linear-gradient(90deg, #90f4e4 0 8px, #4d23cf 8px 10px) !important; border-radius: 0 !important; }"
  ].join("\n");
  var SHADOW_SIMPLE_CSS =
    "#onigiri-reviewer-header .onigiri-reviewer-header-buttons > *:not(:first-child):not(.onigiri-reviewer-progress) { display: none !important; }";

  var C = CHARS.kangel, charKey = "kangel";
  var stream, streamTitle, switchBtn, sprite, chatBox, chatTitle, chatList, hudNums = {}, statNums = {};
  var simple = true, shadowTries = 0, lastCount = -1, phaseSide = "q";
  var base = null, temp = null, tempTimer = null, shown = null;
  var idleAnim = null, idleTimer = null, lastActive = Date.now(), nextIdleAt = FIRST_IDLE[0];
  var recentPicks = [], recentResults = [], lastLine = "", greeted = false;
  var chatNew = null, lastSayAt = 0, nextCheerAt = Date.now() + 25000, sessionStart = Date.now();
  var minutesSaid = {}, nearSaid = -1, streakSaid = 0, recentCheers = [], todayCount = 0;
  var patArea = null, hearts = [], patSession = 0, lastPatAt = 0, lastSfxAt = 0, sfxFlip = false;
  var rubbing = false, rubAt = null, rubDist = 0, patLast = "";
  var TITLE_H = 0, EDGE = 4; // the title bar sits inside the window frame

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function img(file, cls) {
    var node = el("img", cls);
    node.src = A + file;
    node.alt = "";
    return node;
  }
  function win(id) {
    var w = el("div", "wb-win");
    w.id = id;
    var t = el("div", "wb-title");
    w.appendChild(t);
    w.appendChild(el("div", "wb-buttons"));
    return [w, t];
  }
  function rand(range) { return range[0] + Math.random() * (range[1] - range[0]); }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }

  function styleShadow() {
    var host = document.getElementById("onigiri-reviewer-ui-host");
    var root = host && host.shadowRoot;
    if (!root) {
      if (shadowTries++ < 40) setTimeout(styleShadow, 150);
      return;
    }
    var style = root.getElementById("wb-shadow-style");
    if (!style) {
      style = document.createElement("style");
      style.id = "wb-shadow-style";
      root.appendChild(style);
    }
    style.textContent = SHADOW_CSS + (simple ? "\n" + SHADOW_SIMPLE_CSS : "");
  }

  // ── animation player ────────────────────────────────────────────────────

  function show(name, loops) {
    var a = sprite && C.anim[name];
    if (!a) return;
    var key = charKey + ":" + name + ":" + (loops || 0);
    if (key === shown) return;
    shown = key;
    sprite.style.animation = "none";
    sprite.style.backgroundImage = "url('" + A + C.file + name + ".png')";
    sprite.style.backgroundSize = (a[0] * 100) + "% 100%";
    sprite.style.backgroundPosition = "0 0";
    void sprite.offsetWidth; // restart the animation
    sprite.style.animation = "wb-strip " + a[1] + "s steps(" + a[0] + ", jump-none) " +
      (loops ? loops : "infinite") + " forwards";
  }

  function current() {
    if (temp) return;
    if (idleAnim) show(idleAnim.name, idleAnim.loops);
    else show(base);
  }

  // A reaction (answer, milestone, greeting) plays, holds, then hands back.
  function play(name, loops) {
    var a = C.anim[name];
    if (!a) return;
    stopIdle(false);
    loops = loops || (a[0] <= 3 ? 2 : 1);
    temp = name;
    shown = null;
    show(name, loops);
    clearTimeout(tempTimer);
    tempTimer = setTimeout(function () {
      temp = null;
      shown = null;
      current();
    }, a[1] * 1000 * loops + HOLD);
  }

  function setBase(name) {
    base = name;
    if (!temp && !idleAnim) show(base);
  }

  // ── head pats: Ame only, as in the game (hand cursor, hearts, nadenade) ─

  function buildPat(screen) {
    patArea = el("div", "wb-pat");
    ["wb-hearts wb-hearts-r", "wb-hearts wb-hearts-l"].forEach(function (cls) {
      var hrt = el("div", cls);
      screen.appendChild(hrt);
      hearts.push(hrt);
    });
    screen.appendChild(patArea);
    patArea.addEventListener("mousedown", function (e) { e.preventDefault(); }); // keep the typing focus
    patArea.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      rubbing = true;
      rubAt = [e.clientX, e.clientY];
      rubDist = 0;
      pat();
    });
    // Rubbing her head with the button held keeps patting.
    patArea.addEventListener("pointermove", function (e) {
      if (!rubbing || !rubAt) return;
      rubDist += Math.abs(e.clientX - rubAt[0]) + Math.abs(e.clientY - rubAt[1]);
      rubAt = [e.clientX, e.clientY];
      if (rubDist >= 60) {
        rubDist = 0;
        pat();
      }
    });
    ["pointerup", "pointerleave", "pointercancel"].forEach(function (type) {
      patArea.addEventListener(type, function () { rubbing = false; rubAt = null; });
    });
  }

  function heartBurst() {
    hearts.forEach(function (hrt, i) {
      hrt.style.animation = "none";
      void hrt.offsetWidth;
      hrt.style.animation = "wb-strip 0.8s steps(8, jump-none) " + (i ? "0.15s" : "0s") + " 1 both";
    });
  }

  function patLine(pool) {
    var fresh = pool.filter(function (l) { return l[0] !== patLast; });
    var line = pick(fresh.length ? fresh : pool);
    patLast = line[0];
    say(line);
  }

  function pat() {
    if (charKey !== "ame" || !sprite || !C.pat) return;
    var now = Date.now();
    activity(); // wakes her up if she was asleep
    if (now - lastPatAt > 2500) patSession = 0;
    patSession++;
    lastPatAt = now;
    heartBurst();
    if (now - lastSfxAt > 380) {
      lastSfxAt = now;
      sfxFlip = !sfxFlip;
      pycmd("wbsfx:" + (sfxFlip ? "nadenade_1" : "nadenade_2"));
    }
    // A smile at first, then the happy loop while you keep going.
    var face = patSession >= 3 ? "idle_happy" : "smile";
    if (temp !== face) {
      stopIdle(false);
      temp = face;
      shown = null;
      show(face, face === "smile" ? 2 : 0); // the happy loop runs as long as you pat
    }
    clearTimeout(tempTimer);
    tempTimer = setTimeout(function () {
      temp = null;
      shown = null;
      current();
    }, 2200);
    if (patSession === 2) patLine(C.pat.first);
    else if (patSession === 10) patLine(C.pat.more);
    else if (patSession === 25) patLine(C.pat.enough);
  }

  // ── the stream and chat windows move by their title bar ─────────────────

  function chatChrome() {
    return chatBox.getBoundingClientRect().height - chatList.getBoundingClientRect().height;
  }

  function place(w, x, y) {
    var r = w.getBoundingClientRect();
    var minH = w === chatBox ? chatChrome() + 60 : r.height;
    var maxX = window.innerWidth - r.width - EDGE;
    var maxY = window.innerHeight - minH - EDGE;
    w.style.left = Math.round(Math.max(EDGE, Math.min(x, maxX))) + "px";
    w.style.top = Math.round(Math.max(TITLE_H + EDGE, Math.min(y, maxY))) + "px";
    w.style.right = "auto";
    if (w === chatBox) fitChat();
  }

  function raise(w) {
    stream.style.zIndex = w === stream ? 52 : 51;
    chatBox.style.zIndex = w === chatBox ? 52 : 51;
  }

  function savePos(key, w) {
    var r = w.getBoundingClientRect();
    var pos = [Math.round(r.left), Math.round(r.top)];
    window.wbLayout = window.wbLayout || {};
    window.wbLayout[key] = pos;
    pycmd("wbpos:" + key + ":" + pos[0] + "," + pos[1]);
  }

  function resetPos(key, w) {
    w.style.left = w.style.top = w.style.right = "";
    if (window.wbLayout) delete window.wbLayout[key];
    if (w === chatBox) fitChat();
    pycmd("wbpos:" + key + ":reset");
  }

  function draggable(w, key) {
    var t = w.querySelector(".wb-title");
    if (!t) return;
    t.classList.add("wb-drag");
    t.title = "Glisse pour déplacer, double-clic pour remettre en place";
    t.addEventListener("mousedown", function (e) { e.preventDefault(); });
    t.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      var r = w.getBoundingClientRect();
      var dx = e.clientX - r.left, dy = e.clientY - r.top, moved = false;
      try { t.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events */ }
      raise(w);
      document.body.classList.add("wb-dragging");
      function move(ev) {
        moved = true;
        place(w, ev.clientX - dx, ev.clientY - dy);
      }
      function up() {
        t.removeEventListener("pointermove", move);
        t.removeEventListener("pointerup", up);
        t.removeEventListener("pointercancel", up);
        document.body.classList.remove("wb-dragging");
        if (moved) savePos(key, w);
      }
      t.addEventListener("pointermove", move);
      t.addEventListener("pointerup", up);
      t.addEventListener("pointercancel", up);
    });
    t.addEventListener("dblclick", function () { resetPos(key, w); });
  }

  function visible(w) { return w && getComputedStyle(w).display !== "none"; }

  function restorePositions() {
    var saved = window.wbLayout || {};
    if (saved.stream && visible(stream)) place(stream, saved.stream[0], saved.stream[1]);
    if (saved.chat && visible(chatBox)) place(chatBox, saved.chat[0], saved.chat[1]);
  }

  // A smaller window keeps both on screen.
  function reclamp() {
    [stream, chatBox].forEach(function (w) {
      if (w && w.style.left && visible(w)) place(w, parseFloat(w.style.left), parseFloat(w.style.top));
    });
  }

  // ── what she does when nothing happens ─────────────────────────────────

  function mood() {
    var misses = recentResults.slice(-5).filter(function (r) { return !r; }).length;
    var tail = recentResults.slice(-3);
    if (misses >= 3) return "down";
    if (tail.length === 3 && tail.every(function (r) { return r; })) return "happy";
    return "neutral";
  }

  function chooseIdle(stillFor) {
    var hour = new Date().getHours();
    var late = hour >= 23 || hour < 5;
    if (stillFor >= SLEEP_AFTER || (late && Math.random() < LATE_SLEEP)) return pick(C.idle.sleepy);
    var m = mood();
    var pool = (m !== "neutral" && Math.random() < MOOD_WEIGHT) ? C.idle[m] : C.idle.neutral;
    var fresh = pool.filter(function (n) { return recentPicks.indexOf(n) < 0; });
    var choice = pick(fresh.length ? fresh : pool);
    recentPicks.push(choice);
    if (recentPicks.length > 3) recentPicks.shift();
    return choice;
  }

  function startIdle(stillFor) {
    var name = chooseIdle(stillFor);
    var a = C.anim[name];
    var asleep = C.idle.sleepy.indexOf(name) >= 0;
    // Sleep lasts until you move; other activities fill four to seven seconds.
    var loops = asleep ? 0 : Math.max(1, Math.round(rand([4, 7]) / a[1]));
    idleAnim = { name: name, loops: loops, asleep: asleep };
    shown = null;
    show(name, loops);
    var line = C.lines.activity[name];
    if (line && line[0] !== lastLine && Math.random() < 0.6) say(line);
    clearTimeout(idleTimer);
    if (!asleep) {
      idleTimer = setTimeout(function () {
        idleAnim = null;
        shown = null;
        current();
      }, a[1] * 1000 * loops + 300);
      nextIdleAt = stillFor + a[1] * loops + rand(NEXT_IDLE);
    }
  }

  function stopIdle(wokeUp) {
    clearTimeout(idleTimer);
    if (!idleAnim) return;
    var wasAsleep = idleAnim.asleep;
    idleAnim = null;
    shown = null;
    if (wasAsleep && wokeUp) say(pick(C.lines.wake));
    current();
  }

  // You moved or typed: back to the attentive pose, and the clock restarts.
  function activity() {
    lastActive = Date.now();
    nextIdleAt = rand(FIRST_IDLE);
    if (idleAnim) stopIdle(true);
  }

  function tick() {
    if (!sprite) return;
    maybeCheer();
    if (temp || idleAnim) return;
    var stillFor = (Date.now() - lastActive) / 1000;
    if (stillFor >= nextIdleAt) startIdle(stillFor);
  }

  // ── encouragements: only while you are studying, one every 30 to 60 s ──

  function fill(tpl, vars) {
    return tpl.replace(/\{(\w+)\}/g, function (_, k) { return vars[k] != null ? vars[k] : ""; });
  }
  function streak() {
    var s = 0;
    for (var i = recentResults.length - 1; i >= 0 && recentResults[i]; i--) s++;
    return s;
  }
  function cheerLine() {
    var L = C.lines, minutes = Math.floor((Date.now() - sessionStart) / 60000);
    for (var i = MINUTE_MARKS.length - 1; i >= 0; i--) {
      var m = MINUTE_MARKS[i];
      if (minutes >= m) {
        if (!minutesSaid[m]) {
          for (var j = 0; j <= i; j++) minutesSaid[MINUTE_MARKS[j]] = true;
          return [fill(L.minutes[0], { m: m }), fill(L.minutes[1], { m: m })];
        }
        break;
      }
    }
    var next = MILESTONES.filter(function (n) { return n > todayCount; })[0];
    if (next && next - todayCount <= 3 && nearSaid !== todayCount) {
      nearSaid = todayCount;
      var k = next - todayCount, v = { k: k, n: next, cartes: k > 1 ? "cartes" : "carte" };
      return [fill(L.near[0], v), fill(L.near[1], v)];
    }
    var s = streak();
    if (s >= 3 && s !== streakSaid) {
      streakSaid = s;
      return [fill(L.streak[0], { s: s }), fill(L.streak[1], { s: s })];
    }
    var fresh = L.cheer.filter(function (l) { return recentCheers.indexOf(l[0]) < 0; });
    var line = pick(fresh.length ? fresh : L.cheer);
    recentCheers.push(line[0]);
    if (recentCheers.length > 4) recentCheers.shift();
    return line;
  }
  function maybeCheer() {
    var now = Date.now();
    if (now < nextCheerAt) return;
    var studying = now - lastActive < 90000 && !(idleAnim && idleAnim.asleep);
    if (!studying || now - lastSayAt < CHEER_GAP * 1000) {
      nextCheerAt = now + 5000;
      return;
    }
    say(cheerLine());
    nextCheerAt = now + rand(CHEER_EVERY) * 1000;
  }

  // ── status numbers and the talk window ─────────────────────────────────

  function stat(row, key, file, label) {
    var cell = el("div", "wb-stat");
    cell.appendChild(img(file));
    var box = el("div");
    statNums[key] = el("span", null, "0");
    box.appendChild(statNums[key]);
    box.appendChild(el("small", null, label));
    cell.appendChild(box);
    row.appendChild(cell);
  }
  function hudStat(hud, key, file) {
    hud.appendChild(img(file));
    hudNums[key] = el("span", null, "0");
    hud.appendChild(hudNums[key]);
  }
  function setNum(key, n) {
    if (statNums[key]) statNums[key].textContent = String(n);
    if (hudNums[key]) hudNums[key].textContent = String(n);
  }

  // French puts a space before ! ? : ; and inside « »: keep it on the same line.
  function nb(t) {
    return t == null ? t : String(t).replace(/ ([!?:;»])/g, "\u00a0$1").replace(/« /g, "«\u00a0");
  }

  // The chat window ends 12px above the bottom of the screen, whatever its
  // title bar and borders measure: the list scrolls inside it.
  function fitChat() {
    if (!chatBox || !chatList) return;
    var box = chatBox.getBoundingClientRect();
    var chrome = box.height - chatList.getBoundingClientRect().height;
    var room = Math.floor(window.innerHeight - box.top - chrome - 12);
    chatList.style.maxHeight = Math.max(60, room) + "px";
  }

  function atBottom() {
    return chatList.scrollHeight - chatList.scrollTop - chatList.clientHeight < 30;
  }
  function toBottom(smooth) {
    chatList.scrollTo({ top: chatList.scrollHeight, behavior: smooth ? "smooth" : "auto" });
    if (chatNew) chatNew.hidden = true;
  }

  function say(line) {
    if (!chatList || !line) return;
    lastLine = line[0];
    lastSayAt = Date.now();
    var follow = atBottom();
    var li = el("li");
    li.appendChild(img(C.avatar, "wb-avatar"));
    var bubble = el("div", "wb-bubble");
    bubble.appendChild(el("span", "who", C.name));
    bubble.appendChild(el("span", "jp", line[0]));
    bubble.appendChild(el("span", "fr", nb(line[1])));
    li.appendChild(bubble);
    chatList.appendChild(li);
    fitChat();
    while (chatList.children.length > CHAT_KEEP) chatList.removeChild(chatList.firstChild);
    // New lines push the older ones up, unless you scrolled back to read.
    if (follow) toBottom(true);
    else if (chatNew) chatNew.hidden = false;
  }

  function dress() {
    if (!stream) return;
    streamTitle.textContent = C.title;
    chatTitle.textContent = C.talkTitle;
    switchBtn.textContent = "⇄ " + C.other;
    switchBtn.title = "Passer à " + C.other;
    document.body.classList.toggle("wb-char-ame", charKey === "ame");
    document.body.classList.toggle("wb-char-kangel", charKey === "kangel");
  }

  function build() {
    if (stream || !document.body) return;

    var w = win("wb-stream");
    stream = w[0]; streamTitle = w[1];
    switchBtn = el("button", "wb-switch");
    switchBtn.type = "button";
    switchBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      pycmd("wbchar:" + (charKey === "kangel" ? "ame" : "kangel"));
    });
    stream.appendChild(switchBtn);
    var screen = el("div", "wb-screen");
    sprite = el("div", "wb-kangel");
    screen.appendChild(sprite);
    buildPat(screen);
    stream.appendChild(screen);
    var row = el("div", "wb-status");
    stat(row, "count", "st_follower.png", "aujourd'hui");
    stat(row, "good", "st_love.png", "réussies");
    stat(row, "again", "st_stress.png", "à revoir");
    stream.appendChild(row);
    document.body.appendChild(stream);

    var c = win("wb-chat");
    chatBox = c[0]; chatTitle = c[1];
    chatList = el("ul");
    chatBox.appendChild(chatList);
    chatNew = el("button", "wb-chat-new", "▼ nouveaux messages");
    chatNew.type = "button";
    chatNew.hidden = true;
    chatNew.addEventListener("click", function () { toBottom(true); });
    chatBox.appendChild(chatNew);
    chatList.addEventListener("scroll", function () { if (atBottom()) chatNew.hidden = true; }, { passive: true });
    document.body.appendChild(chatBox);
    fitChat();
    draggable(stream, "stream");
    draggable(chatBox, "chat");
    restorePositions();
    window.addEventListener("resize", function () { reclamp(); fitChat(); });

    var hud = el("div");
    hud.id = "wb-hud";
    hudStat(hud, "count", "st_follower.png");
    hudStat(hud, "good", "st_love.png");
    hudStat(hud, "again", "st_stress.png");
    document.body.appendChild(hud);

    dress();
    ["mousemove", "mousedown", "keydown", "wheel", "input", "touchstart"].forEach(function (type) {
      document.addEventListener(type, activity, { passive: true, capture: true });
    });
    setInterval(tick, 1000);
    styleShadow();
  }

  function greet(lines) {
    say(pick(lines));
    play(C.start);
  }

  window.wbStream = {
    update: function (data) {
      simple = data.simple !== false;
      if (data.character && CHARS[data.character]) {
        charKey = data.character;
        C = CHARS[charKey];
      }
      build();
      dress();
      styleShadow();
      if (chatBox) chatBox.style.visibility = data.chat ? "" : "hidden";
      var n = data.count || 0;
      todayCount = n;
      setNum("count", n);
      setNum("good", data.good || 0);
      setNum("again", data.again || 0);
      phaseSide = "q";
      activity();
      setBase(C.question);
      if (!greeted) { greeted = true; greet(C.lines.start); }
      else if (n !== lastCount && lastCount >= 0 && C.lines.milestone[n]) {
        say(C.lines.milestone[n]);
        play(C.milestone);
      }
      lastCount = n;
    },
    phase: function (side) {
      build();
      phaseSide = side;
      activity();
      setBase(side === "a" ? C.answer : C.question);
    },
    react: function (mood, line) {
      build();
      if (mood === "learn") {
        // Not knowing a new card is not a miss: her mood does not drop.
        say(line || pick(C.lines.oops));
        play(pick(C.learn));
        return;
      }
      var good = mood !== "oops";
      recentResults.push(good);
      if (recentResults.length > 8) recentResults.shift();
      say(pick(good ? C.lines.yay : C.lines.oops));
      play(pick(good ? C.yay : C.oops));
    },
    setCharacter: function (key) {
      if (!CHARS[key]) return;
      build();
      charKey = key;
      C = CHARS[key];
      temp = null; idleAnim = null; shown = null;
      clearTimeout(tempTimer); clearTimeout(idleTimer);
      recentPicks = [];
      recentCheers = [];
      if (chatList) chatList.textContent = "";
      if (chatNew) chatNew.hidden = true;
      dress();
      activity();
      base = phaseSide === "a" ? C.answer : C.question;
      greet(C.lines.hello);
    },
    // For the dev tour: start an activity now, as if you had been still that long.
    debugIdle: function (seconds) { if (!temp) startIdle(seconds || 10); },
    debugCheer: function (n) { for (var i = 0; i < (n || 1); i++) say(cheerLine()); },
    debugPat: function (n) { for (var i = 0; i < (n || 1); i++) { lastSfxAt = 0; pat(); } },
    debugInfo: function () { return { charKey: charKey, sprite: !!sprite, pat: !!C.pat, name: C.name, temp: temp }; }
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
