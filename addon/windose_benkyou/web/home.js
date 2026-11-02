// Windose Benkyou: the taskbar on the deck list and deck overview, with a
// working Start menu (the game's menu panel and desktop icons) and a clock.
// Each menu entry sends "wbstart:<action>" to the add-on, which runs it in Anki.
(function () {
  if (window.wbTaskbar) return;
  window.wbTaskbar = true;

  var ITEMS = [
    ["study", "Étudier Kaishi", "べんきょう"],
    ["decks", "Mes paquets", "デッキ"],
    ["add", "Ajouter une carte", "ついか"],
    ["browse", "Parcourir les cartes", "さがす"],
    ["stats", "Statistiques", "ステータス"],
    ["sync", "Synchroniser", "AnkiWeb"],
    ["char", "", ""],
    ["voice", "", ""],
    ["settings", "Modules et réglages", "せってい"],
    ["quit", "Quitter", "おやすみ"]
  ];

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function build() {
    if (document.getElementById("wb-taskbar") || !document.body) return;

    var bar = el("div");
    bar.id = "wb-taskbar";
    var start = el("button", null, "スタート");
    start.id = "wb-start";
    start.type = "button";
    start.title = "Menu";
    start.setAttribute("aria-haspopup", "menu");
    start.setAttribute("aria-expanded", "false");
    bar.appendChild(start);
    bar.appendChild(el("div", "wb-task", "べんきょう.exe"));
    var tray = el("div");
    tray.id = "wb-tray";
    var clock = el("span");
    tray.appendChild(clock);
    bar.appendChild(tray);

    var menu = el("div");
    menu.id = "wb-menu";
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    ITEMS.forEach(function (item) {
      var b = el("button", "wb-menu-item");
      b.type = "button";
      b.setAttribute("role", "menuitem");
      b.dataset.action = item[0];
      var icon = el("span", "wb-menu-icon wb-i-" + item[0]);
      var label = el("span", "wb-menu-label", item[1]);
      var jp = el("span", "wb-menu-jp", item[2]);
      b.appendChild(icon);
      b.appendChild(label);
      b.appendChild(jp);
      if (item[0] === "char") {
        // Shows who you would switch to; the add-on remembers the choice.
        var paint = function () {
          var toAme = (window.wbCharacter || "kangel") === "kangel";
          label.textContent = toAme ? "Passer à Ame" : "Passer à KAngel";
          jp.textContent = toAme ? "あめちゃん" : "超てんちゃん";
          icon.className = "wb-menu-icon " + (toAme ? "wb-i-ame" : "wb-i-kangel");
        };
        paint();
        b.addEventListener("click", function () {
          window.wbCharacter = (window.wbCharacter || "kangel") === "kangel" ? "ame" : "kangel";
          paint();
          close();
          pycmd("wbchar:" + window.wbCharacter);
        });
      } else if (item[0] === "voice") {
        // Her voice on the cards, or the original recordings (NHK, JLPT Tango).
        var paintVoice = function () {
          var hers = (window.wbVoice || "character") === "character";
          label.textContent = hers ? "Voix : la sienne" : "Voix : d'origine";
          jp.textContent = hers ? "こえ ♡" : "こえ NHK";
        };
        paintVoice();
        b.addEventListener("click", function () {
          window.wbVoice = (window.wbVoice || "character") === "character" ? "original" : "character";
          paintVoice();
          close();
          pycmd("wbvoice:" + window.wbVoice);
        });
      } else {
        b.addEventListener("click", function () {
          close();
          pycmd("wbstart:" + item[0]);
        });
      }
      menu.appendChild(b);
    });

    function open() {
      menu.hidden = false;
      start.classList.add("wb-pressed");
      start.setAttribute("aria-expanded", "true");
      var first = menu.querySelector("button");
      if (first) first.focus();
    }
    function close() {
      menu.hidden = true;
      start.classList.remove("wb-pressed");
      start.setAttribute("aria-expanded", "false");
    }

    start.addEventListener("click", function (e) {
      e.stopPropagation();
      if (menu.hidden) open(); else close();
    });
    document.addEventListener("click", function (e) {
      if (!menu.hidden && !menu.contains(e.target)) close();
    });
    document.addEventListener("keydown", function (e) {
      if (menu.hidden) return;
      var items = Array.prototype.slice.call(menu.querySelectorAll("button"));
      var i = items.indexOf(document.activeElement);
      if (e.key === "Escape") { close(); start.focus(); e.preventDefault(); }
      else if (e.key === "ArrowDown") { items[(i + 1) % items.length].focus(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { items[(i - 1 + items.length) % items.length].focus(); e.preventDefault(); }
    });

    function tick() {
      var d = new Date();
      clock.textContent = ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
    }
    tick();
    setInterval(tick, 15000);

    document.body.appendChild(menu);
    document.body.appendChild(bar);
    window.wbOpenStart = open;
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
