/* MADHOUSE Telegram Clean — shared behaviour.
   Everything here works offline in a browser and inside Telegram.
   No engine call, no tracking, no phone number, no login.
   Skins and worlds are local choices, saved only on this device. */
(function () {
  "use strict";
  var tg = (window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;
  if (tg) { try { tg.expand(); tg.ready(); } catch (e) {} }
  function haptic(kind) {
    if (!tg || !tg.HapticFeedback) return;
    try {
      if (kind === "ok") tg.HapticFeedback.notificationOccurred("success");
      else if (kind === "bad") tg.HapticFeedback.notificationOccurred("error");
      else tg.HapticFeedback.impactOccurred("light");
    } catch (e) {}
  }
  var soundOn = true;
  try { soundOn = localStorage.getItem("mh-sound") !== "off"; } catch (e) {}
  function beep(freq) {
    if (!soundOn) return;
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      var ctx = new Ctx(), o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.value = freq || 659; o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0.08, ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
      o.start(); o.stop(ctx.currentTime + 0.26);
    } catch (e) {}
  }
  var SKINS = {
    "Vibrant Welcome": ["#faf6ee", "#1d1a16", "#ffd23f"],
    "Neon Carnival": ["#111827", "#f9fafb", "#ec4899"],
    "Golden Caravan": ["#fff8e1", "#3e2723", "#f5c518"],
    "Cosmic Night": ["#0a1a2e", "#ffffff", "#7c3aed"],
    "Ocean Bright": ["#e0f7fa", "#00363a", "#0891b2"],
    "Jester Party": ["#fdf2f8", "#3b0764", "#f97316"]
  };
  var WORLDS = ["Snowman World", "Teddy Bear World", "Jester Island", "Consul",
    "Olympus", "Bermuda Triangle", "Libra Land", "Zorbians", "Xiorbs", "Xorbs"];
  function applySkin(name) {
    var s = SKINS[name] || SKINS["Vibrant Welcome"];
    var r = document.documentElement.style;
    r.setProperty("--bg", s[0]); r.setProperty("--ink", s[1]); r.setProperty("--gold", s[2]);
    try { localStorage.setItem("mh-skin", name); } catch (e) {}
    var el = document.getElementById("skinName");
    if (el) el.textContent = name;
  }
  function applyWorld(name) {
    try { localStorage.setItem("mh-world", name); } catch (e) {}
    var el = document.getElementById("worldName");
    if (el) el.textContent = name;
  }
  function showAnswer(id, html) {
    var el = document.getElementById(id);
    if (el) { el.innerHTML = html; el.style.display = "block"; }
    haptic("ok"); beep(659);
  }
  window.MH = {
    tg: tg, haptic: haptic, beep: beep, showAnswer: showAnswer,
    skins: Object.keys(SKINS), worlds: WORLDS, applySkin: applySkin, applyWorld: applyWorld,
    soundOn: function () { return soundOn; },
    setSound: function (on) {
      soundOn = !!on;
      try { localStorage.setItem("mh-sound", soundOn ? "on" : "off"); } catch (e) {}
    }
  };
  document.addEventListener("DOMContentLoaded", function () {
    var savedSkin = null, savedWorld = null;
    try { savedSkin = localStorage.getItem("mh-skin"); savedWorld = localStorage.getItem("mh-world"); } catch (e) {}
    if (savedSkin && SKINS[savedSkin]) applySkin(savedSkin);
    if (savedWorld) applyWorld(savedWorld);
    var skinSel = document.getElementById("skinSelect");
    if (skinSel) {
      Object.keys(SKINS).forEach(function (n) {
        var o = document.createElement("option"); o.value = n; o.textContent = n; skinSel.appendChild(o);
      });
      if (savedSkin) skinSel.value = savedSkin;
      skinSel.addEventListener("change", function () { applySkin(skinSel.value); beep(659); });
    }
    var worldSel = document.getElementById("worldSelect");
    if (worldSel) {
      WORLDS.forEach(function (n) {
        var o = document.createElement("option"); o.value = n; o.textContent = n; worldSel.appendChild(o);
      });
      if (savedWorld) worldSel.value = savedWorld;
      worldSel.addEventListener("change", function () { applyWorld(worldSel.value); beep(784); });
    }
    var soundBtn = document.getElementById("soundToggle");
    if (soundBtn) {
      soundBtn.textContent = soundOn ? "🔊 Sound: on — tap to turn off" : "🔇 Sound: off — tap to turn on";
      soundBtn.addEventListener("click", function () {
        window.MH.setSound(!window.MH.soundOn());
        soundBtn.textContent = window.MH.soundOn() ? "🔊 Sound: on — tap to turn off" : "🔇 Sound: off — tap to turn on";
        beep(659);
      });
    }
    var sizeBtn = document.getElementById("sizeToggle");
    if (sizeBtn) {
      sizeBtn.addEventListener("click", function () {
        document.body.style.fontSize = (document.body.style.fontSize === "22px") ? "19px" : "22px";
        sizeBtn.textContent = (document.body.style.fontSize === "22px") ? "🔎 Text: large — tap for normal" : "🔎 Text: normal — tap for large";
        beep(659);
      });
    }
  });
})();
