// Windose Benkyou: answer before you see the correction.
// Under the question, a "こたえ.exe" window asks for the meaning in French and
// the reading, typed in romaji and turned into hiragana as you type. Enter
// sends both to the add-on, which checks them and shows the answer. The result
// window then moves above the card and the right grade is proposed.
(function () {
  if (window.wbQuiz) return;

  var BASE = ((document.currentScript && document.currentScript.src) || "").replace(/quiz\.js.*$/, "");
  var AVATAR = { kangel: "icon_kangel.png", ame: "jine_ame.png" };

  // ── romaji to hiragana ──────────────────────────────────────────────────
  var T = {};
  function add(prefix, list) {
    for (var i = 0; i < 5; i++) if (list[i]) T[prefix + "aiueo"[i]] = list[i];
  }
  add("", ["あ", "い", "う", "え", "お"]);
  add("k", "かきくけこ".split("")); add("g", "がぎぐげご".split(""));
  add("s", "さしすせそ".split("")); add("z", "ざじずぜぞ".split(""));
  add("t", "たちつてと".split("")); add("d", "だぢづでど".split(""));
  add("n", "なにぬねの".split("")); add("h", "はひふへほ".split(""));
  add("b", "ばびぶべぼ".split("")); add("p", "ぱぴぷぺぽ".split(""));
  add("m", "まみむめも".split("")); add("r", "らりるれろ".split(""));
  add("l", "らりるれろ".split(""));
  add("y", ["や", "い", "ゆ", "いぇ", "よ"]); add("w", ["わ", "うぃ", "う", "うぇ", "を"]);
  add("f", ["ふぁ", "ふぃ", "ふ", "ふぇ", "ふぉ"]); add("v", ["ゔぁ", "ゔぃ", "ゔ", "ゔぇ", "ゔぉ"]);
  add("x", "ぁぃぅぇぉ".split(""));
  add("sh", ["しゃ", "し", "しゅ", "しぇ", "しょ"]); add("ch", ["ちゃ", "ち", "ちゅ", "ちぇ", "ちょ"]);
  add("j", ["じゃ", "じ", "じゅ", "じぇ", "じょ"]); add("ts", ["つぁ", "つぃ", "つ", "つぇ", "つぉ"]);
  var YOON = { k: "き", g: "ぎ", n: "に", h: "ひ", b: "び", p: "ぴ", m: "み", r: "り", l: "り",
               s: "し", z: "じ", j: "じ", t: "ち", c: "ち", d: "ぢ" };
  for (var c0 in YOON) add(c0 + "y", [YOON[c0] + "ゃ", YOON[c0] + "ぃ", YOON[c0] + "ゅ", YOON[c0] + "ぇ", YOON[c0] + "ょ"]);
  T.xya = "ゃ"; T.xyu = "ゅ"; T.xyo = "ょ"; T.xtu = "っ"; T.xtsu = "っ"; T.ltu = "っ";
  T.thi = "てぃ"; T.dhi = "でぃ"; T.dhu = "でゅ"; T["-"] = "ー";

  function toKana(str, final) {
    var s = String(str || "").toLowerCase(), out = "", i = 0;
    while (i < s.length) {
      var c = s[i], nx = s[i + 1];
      if (!/[a-z'\-]/.test(c)) { out += c; i++; continue; }
      if (c === "n") {
        if (nx === undefined) { out += final ? "ん" : "n"; i++; continue; }
        if (nx === "'") { out += "ん"; i += 2; continue; }
        if (nx === "n") {
          // "konna": the second n starts な; "honn": both n make one ん.
          if (s[i + 2] !== undefined && /[aiueoy]/.test(s[i + 2])) { out += "ん"; i += 1; }
          else { out += "ん"; i += 2; }
          continue;
        }
        if (!/[aiueoy]/.test(nx)) { out += "ん"; i++; continue; }
      }
      if ((c === nx && /[bcdfghjkmpqrstvwxz]/.test(c)) || (c === "t" && nx === "c")) {
        out += "っ"; i++; continue;
      }
      var hit = false;
      for (var L = 4; L >= 1; L--) {
        var chunk = s.substr(i, L);
        if (T[chunk]) { out += T[chunk]; i += L; hit = true; break; }
      }
      if (!hit) { if (c !== "'") out += c; i++; }
    }
    return out;
  }

  // ── the answer window ───────────────────────────────────────────────────
  var box, body, askPart, meaningRow, readingRow, meaningIn, readingIn, resultPart;
  var active = false, submitted = false, needMeaning = true, needReading = true;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  // French puts a space before ! ? : ; and inside « »: keep it on the same line.
  function nb(t) {
    return t == null ? t : String(t).replace(/ ([!?:;»])/g, "\u00a0$1").replace(/« /g, "«\u00a0");
  }

  function field(label, hint, id, placeholder) {
    var row = el("label", "wb-q-row");
    row.setAttribute("for", id);
    var name = el("span", "wb-q-name", label);
    name.appendChild(el("small", null, hint));
    row.appendChild(name);
    var input = el("input", "wb-q-input");
    input.id = id;
    input.type = "text";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.placeholder = placeholder;
    row.appendChild(input);
    return [row, input];
  }

  function build() {
    if (box || !document.body) return;
    box = el("div", "wb-win");
    box.id = "wb-quiz";
    var title = el("div", "wb-title", "こたえ.exe");
    box.appendChild(title);
    box.appendChild(el("div", "wb-buttons"));
    body = el("div", "wb-q-body");

    askPart = el("div", "wb-q-ask");
    var m = field("Sens", "en français", "wb-q-meaning", "ex. moi");
    meaningRow = m[0]; meaningIn = m[1];
    var r = field("Lecture", "tape en romaji", "wb-q-reading", "ex. watashi → わたし");
    readingRow = r[0]; readingIn = r[1];
    readingIn.lang = "ja";
    askPart.appendChild(meaningRow);
    askPart.appendChild(readingRow);
    var actions = el("div", "wb-q-actions");
    var skip = el("button", "wb-q-skip", "Je ne sais pas");
    skip.type = "button";
    skip.addEventListener("click", function () { submit(true); });
    actions.appendChild(skip);
    actions.appendChild(el("span", "wb-q-hint", "Entrée : valider"));
    askPart.appendChild(actions);
    body.appendChild(askPart);

    resultPart = el("div", "wb-q-result");
    body.appendChild(resultPart);
    box.appendChild(body);

    readingIn.addEventListener("input", function () {
      var v = toKana(readingIn.value, false);
      if (v !== readingIn.value) readingIn.value = v;
    });
    [meaningIn, readingIn].forEach(function (input) {
      input.addEventListener("keydown", function (e) {
        if (e.key !== "Enter" || e.isComposing) return;
        e.preventDefault();
        e.stopPropagation();
        if (input === meaningIn && needReading && !readingIn.value.trim()) readingIn.focus();
        else submit(false);
      });
    });
  }

  function place(beforeCard) {
    var qa = document.getElementById("qa");
    if (!qa || !box) return;
    qa.parentNode.insertBefore(box, beforeCard ? qa : qa.nextSibling);
  }

  function values() {
    return {
      meaning: needMeaning ? meaningIn.value.trim() : "",
      reading: needReading ? toKana(readingIn.value, true).trim() : ""
    };
  }

  function submit(skipped) {
    if (!active || submitted) return;
    submitted = true;
    var v = skipped ? { meaning: "", reading: "", skipped: true } : values();
    pycmd("wbquiz:" + JSON.stringify(v));
  }

  // ○ right, △ still to learn (orange), ✕ wrong on a card already learned.
  function mark(state) {
    var sym = state === "ok" ? "○" : (state === "learn" ? "△" : "✕");
    return el("span", "wb-q-mark wb-" + state, sym);
  }

  function resultRow(label, part, learn) {
    var row = el("div", "wb-q-line");
    row.appendChild(mark(part.ok ? "ok" : (learn ? "learn" : "ko")));
    row.appendChild(el("span", "wb-q-name", label));
    row.appendChild(el("span", "wb-q-typed", part.typed ? "« " + part.typed + " »" : "(vide)"));
    var note = part.ok ? (part.close ? "presque, faute de frappe" : "juste") : "réponse : " + part.expected;
    row.appendChild(el("span", "wb-q-note", note));
    return row;
  }

  // KAngel or Ame explains the card: reading, meaning, an example with
  // furigana, a tip from the card's notes.
  function lesson(l) {
    var wrap = el("div", "wb-lesson");
    var av = el("img", "wb-avatar");
    av.src = BASE + "assets/" + (AVATAR[l.char] || AVATAR.kangel);
    av.alt = "";
    wrap.appendChild(av);
    var bub = el("div", "wb-bubble");
    bub.appendChild(el("span", "who", l.who));
    if (l.intro) {
      bub.appendChild(el("span", "jp", l.intro[0]));
      bub.appendChild(el("span", "fr", nb(l.intro[1])));
    }
    (l.lines || []).forEach(function (t) { bub.appendChild(el("p", "wb-l-line", nb(t))); });
    if (l.example && l.example.length) {
      var ex = el("div", "wb-l-ex");
      ex.appendChild(el("span", "wb-l-tag", "Exemple"));
      var jp = el("span", "wb-l-jp");
      jp.lang = "ja";
      l.example.forEach(function (seg) {
        var node;
        if (seg[1]) {
          node = el("ruby");
          node.appendChild(document.createTextNode(seg[0]));
          node.appendChild(el("rt", null, seg[1]));
        } else {
          node = document.createTextNode(seg[0]);
        }
        if (seg[2]) {
          var b = el("b");
          b.appendChild(node);
          node = b;
        }
        jp.appendChild(node);
      });
      ex.appendChild(jp);
      if (l.example_fr) ex.appendChild(el("span", "wb-l-fr", nb(l.example_fr)));
      bub.appendChild(ex);
    }
    if (l.tip) bub.appendChild(el("p", "wb-l-tip", nb("Astuce : " + l.tip)));
    if (l.outro) {
      bub.appendChild(el("span", "jp wb-l-outro", l.outro[0]));
      bub.appendChild(el("span", "fr", nb(l.outro[1])));
    }
    wrap.appendChild(bub);
    return wrap;
  }

  window.wbQuiz = {
    toKana: toKana,
    ask: function (opts) {
      build();
      active = true;
      submitted = false;
      needMeaning = opts.needMeaning !== false;
      needReading = opts.needReading !== false;
      box.className = "wb-win wb-q-asking";
      box.style.marginTop = "";
      box.style.marginBottom = "";
      box.querySelector(".wb-title").textContent = "こたえ.exe";
      meaningIn.value = "";
      readingIn.value = "";
      meaningRow.style.display = needMeaning ? "" : "none";
      readingRow.style.display = needReading ? "" : "none";
      // Sentence cards (JLPT Tango): the question is the word in pink, not the sentence.
      meaningRow.querySelector("small").textContent = opts.inSentence ? "du mot en rose, en français" : "en français";
      readingRow.querySelector("small").textContent = opts.inSentence ? "du mot en rose, en romaji" : "tape en romaji";
      resultPart.textContent = "";
      box.style.display = "";
      place(false);
      setTimeout(function () { (needMeaning ? meaningIn : readingIn).focus(); }, 30);
    },
    values: function () { return active ? values() : null; },
    submit: submit,
    verdict: function (data) {
      build();
      active = false;
      var learn = !data.ok && !!data.learn;
      var state = data.ok ? "ok" : (learn ? "learn" : "ko");
      box.className = "wb-win wb-q-done " + (data.ok ? "wb-q-right" : (learn ? "wb-q-learn" : "wb-q-wrong"));
      box.querySelector(".wb-title").textContent = learn ? "レッスン.exe" : "けっか.exe";
      resultPart.textContent = "";
      var head = el("div", "wb-q-head");
      head.appendChild(mark(state));
      head.appendChild(el("span", null, data.ok ? "Juste !" : (learn ? "À apprendre" : "Pas tout à fait")));
      resultPart.appendChild(head);
      if (!data.skipped && !data.empty) {
        if (data.meaning) resultPart.appendChild(resultRow("Sens", data.meaning, learn));
        if (data.reading) resultPart.appendChild(resultRow("Lecture", data.reading, learn));
      }
      if (learn && data.lesson) resultPart.appendChild(lesson(data.lesson));
      var next = el("p", "wb-q-next");
      next.appendChild(document.createTextNode("Entrée = "));
      next.appendChild(el("b", null, data.suggest));
      next.appendChild(document.createTextNode(nb(learn
        ? ". Tu la connaissais en fait ? Clique Correct en bas."
        : ". Pas d'accord ? Clique l'autre bouton en bas.")));
      resultPart.appendChild(next);
      box.style.display = "";
      place(true);
      // Onigiri pushes the card down with an inline !important margin to clear
      // its header. Now the result window sits above the card, so a negative
      // bottom margin collapses with it and leaves a small, even gap.
      var qa = document.getElementById("qa");
      var pushed = qa ? parseFloat(getComputedStyle(qa).marginTop) || 0 : 0;
      box.style.marginBottom = (14 - pushed) + "px";
      window.scrollTo(0, 0);
    },
    off: function () {
      active = false;
      if (box) box.style.display = "none";
    }
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
