// Chaski demo rehearsal — the timeline. All times come from window.DATA (build.py), which comes from the VO alignment.
(function () {
  var DATA = window.DATA, E = DATA.ev, D = E.TOTAL;
  var UI = MS.SPRINGS.ui, ST = MS.SPRINGS.settle;
  var UI_E = MS.springEase(UI.zeta), UI_D = MS.springDur(UI.zeta, UI.omega);   // objects land, ~5 % overshoot
  var ST_E = MS.springEase(ST.zeta), ST_D = MS.springDur(ST.zeta, ST.omega);   // words settle, no overshoot
  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function ok(v, n) { if (!isFinite(v)) throw new Error("NaN time: " + n); return v; }        // gotcha 23

  document.fonts.ready.then(function () {
    var tl = gsap.timeline({ paused: true });
    function ft(el, from, to, at) { to.immediateRender = false; return tl.fromTo(el, from, to, ok(at, el)); }
    function land(el, at) { return ft(el, { y: 200, scale: 0.5, rotation: -9, opacity: 0 }, { y: 0, scale: 1, rotation: 0, opacity: 1, duration: UI_D, ease: UI_E }, at); }
    function rise(el, at, dy) { return ft(el, { y: dy || 36, opacity: 0 }, { y: 0, opacity: 1, duration: ST_D, ease: ST_E }, at); }
    function fade(el, at, d, to) { return ft(el, { opacity: to ? 0 : 1 }, { opacity: to ? 1 : 0, duration: d || 0.25, ease: "power2.out" }, at); }
    function show(el, at) { return fade(el, at, 0.25, true); }
    function avatar(pid, state, at) {           // the vicuña's state, swapped with a short crossfade
      $$("#ava-" + pid + " .st").forEach(function (img) {
        var on = img.classList.contains("st-" + state);
        tl.to(img, { opacity: on ? 1 : 0, duration: 0.18, ease: "power1.inOut" }, ok(at, "ava"));
      });
    }

    /* ── HUD + caption colour follow the field ── */

    /* ── direction cards: stacked in the right column, land on the UI spring ── */
    var cols = {};
    $$(".card").forEach(function (c) {
      var pid = c.id.split("-")[1];
      cols[pid] = cols[pid] || 0;
      c.style.top = cols[pid] + "px";
      cols[pid] += c.offsetHeight + 22;
      land(c, parseFloat(c.dataset.at));
    });

    /* ── captions: each word rises as it is spoken ── */
    $$(".cap").forEach(function (cap) {
      var ws = $$(".w", cap), who = $(".cwho", cap);
      if (who) show(who, parseFloat(ws[0].dataset.t) - 0.05);
      ws.forEach(function (w) { ft(w, { y: 26, opacity: 0 }, { y: 0, opacity: 1, duration: 0.32, ease: ST_E }, parseFloat(w.dataset.t)); });
    });

    /* ═══ intro ═══ */
    ft("#i-ava", { y: 60 * 0.5, opacity: 0.5, scale: 0.92 }, { y: 0, opacity: 1, scale: 1, duration: UI_D, ease: UI_E }, 0);   // frame 0 is a poster
    rise("#i-t1", 0.25, 60); rise("#i-t2", 0.45, 60);
    rise("#i-l1", 2.0); rise("#i-l2", 3.4); rise("#i-l3", 5.0);

    /* ═══ B1 · who it's for, three pills on his words ═══ */
    land("#w1", E.w_interp); land("#w2", E.w_nurse); land("#w3", E.w_silent);

    /* ═══ B1 · her video (12.5 s) ═══ */
    land("#lap", E.mama - 0.78);
    rise("#mama-name", E.mama + 1.0);

    /* ═══ B2→B3 · speak to the phone, it thinks, Chaski speaks ═══ */
    land("#ph-b2b", E.s02 - 0.35);
    land("#sc1", E.w_nine); land("#sc2", E.w_one5); land("#sc3", E.w_pill);
    avatar("b2b", "escuchando", E.s03 - 0.1);
    show("#m-es", E.s03);
    var ew = $$("#m-es .ew"), es = DATA.caps.filter(function (c) { return c.seg === "s03"; });
    var esWords = [].concat.apply([], es.map(function (c) { return c.words; }));
    ew.forEach(function (w, i) { ft(w, { opacity: 0.18 }, { opacity: 1, duration: 0.2 }, esWords[Math.min(i, esWords.length - 1)].t); });
    avatar("b2b", "pensando", E.think);
    var stepsT = [E.think, E.think + 2.6, E.think + 5.3];
    $$("#steps-b2b .step").forEach(function (s, i) {
      rise(s, stepsT[i], 14);
      tl.set(s, { className: "step done" }, stepsT[i] + 2.4);
    });
    ft("#steps-b2b", { opacity: 1 }, { opacity: 0, duration: 0.2 }, E.q_b3 - 0.3);
    land("#m-qu", E.q_b3 - 0.25);
    avatar("b2b", "hablando", E.q_b3);
    var qw = $$("#m-qu .qw"), qd = 7.3 / qw.length;
    qw.forEach(function (w, i) { ft(w, { opacity: 0.18 }, { opacity: 1, duration: 0.15 }, E.q_b3 + i * qd); });
    land("#m-ok", E.q_b3 + 7.4);
    avatar("b2b", "reposo", E.q_b3 + 7.6);

    /* ═══ B3 · how it was checked, a chain of five ═══ */
    [E.w_back, E.w_code, E.w_tea].forEach(function (at, i) { land("#ch" + i, at); });

    /* ═══ B3 · the patient answers ═══ */
    land("#ph-b3b", E.pac - 0.6);
    show("#p-qu", E.pac);
    $$("#p-wave i").forEach(function (b, i) {
      ft(b, { scaleY: 0.3 }, { scaleY: 1, duration: 0.18, ease: "sine.inOut", repeat: Math.floor((5.8 - 0.2) / 0.36), yoyo: true }, E.pac + i * 0.02);
    });
    avatar("b3b", "pensando", E.pac + 6.0);
    $$("#steps-b3b .step").forEach(function (s, i) { rise(s, E.pac + 6.1 + i * 1.0, 14); tl.set(s, { className: "step done" }, E.pac + 6.9 + i * 1.0); });
    ft("#steps-b3b", { opacity: 1 }, { opacity: 0, duration: 0.15 }, E.pac_es - 0.2);
    land("#p-es", E.pac_es);
    avatar("b3b", "hablando", E.pac_es);
    avatar("b3b", "reposo", E.pac_es + 2.5);

    /* ═══ B3 · emergency mode: two taps, instant ═══ */
    land("#ph-b3c", PAGESTART("b3c"));
    show("#e-btn", PAGESTART("b3c") + 0.3);
    ft("#e-btn", { scale: 1 }, { scale: 0.9, duration: 0.08, yoyo: true, repeat: 1 }, E.tap1);
    fade("#e-btn", E.tap1 + 0.2, 0.15);
    land("#e-grid", E.tap1 + 0.25);
    ft("#eg-0", { scale: 1 }, { scale: 0.92, duration: 0.08, yoyo: true, repeat: 1 }, E.tap2);
    fade("#e-grid", E.tap2 + 0.2, 0.15);
    land("#e-card", E.q_em - 0.1);
    land("#e-card .chip", E.q_em + 0.6);
    avatar("b3c", "hablando", E.q_em); avatar("b3c", "reposo", E.q_em + 1.6);

    /* ═══ B4 · the refusal ═══ */
    land("#ph-b4", PAGESTART("b4") + 0.05);
    show("#r-es", E.s08 + 0.6);
    land("#r-ban", E.s08 + 1.4);
    avatar("b4", "pensando", E.s08 + 1.5);
    land("#r-red", E.red);
    avatar("b4", "no_entendi", E.red);

    /* ═══ B5 · Ricardo's one slide ═══ */
    land("#sl", PAGESTART("b5") + 0.1);
    land("#sl0", E.w_four); land("#sl2", E.w_opus); land("#sl3", E.w_184);

    /* ═══ B6 · the summary of this visit ═══ */
    land("#ph-b6", PAGESTART("b6") + 0.05);
    land("#s-1", E.w_note); land("#s-2", E.w_home); land("#s-3", E.w_words);

    /* ═══ end ═══ */
    land("#e-ava", PAGESTART("end") + 0.05); rise("#e-t1", PAGESTART("end") + 0.25, 60);
    rise("#e-l1", PAGESTART("end") + 3.6); rise("#e-l2", PAGESTART("end") + 4.2);

    function PAGESTART(id) { for (var i = 0; i < DATA.pages.length; i++) if (DATA.pages[i].id === id) return DATA.pages[i].start; throw new Error(id); }

    /* ── the pitch clock + bar, a pure function of t; holds drift ≈ 1 %/s ── */
    var clk = $("#clk"), fill = $("#barfill"), hud = $("#hud"), caps = $("#caps");
    var stages = $$(".stage");
    MS.drive(tl, D, function (t) {
      var pt = Math.max(0, Math.min(t - E.T0, DATA.pitch_len));
      var m = Math.floor(pt / 60), s = Math.floor(pt % 60);
      clk.textContent = m + ":" + (s < 10 ? "0" : "") + s;
      fill.style.transform = "scaleX(" + Math.min(1, pt / 180).toFixed(4) + ")";
      var dark = false;
      DATA.pages.forEach(function (p) { if (t >= p.start) dark = p.dark; });
      hud.className = (dark ? "ondark" : "") + (pt > 180 ? " over" : "");
      caps.className = dark ? "ondark" : "";
      DATA.pages.forEach(function (p, i) {
        var k = p.id === "b1" ? 1 : 1 + 0.006 * Math.max(0, Math.min(t, p.end) - p.start);
        stages[i].style.transform = "scale(" + Math.min(k, 1.06).toFixed(5) + ")";
      });
    });

    window.__timelines = window.__timelines || {};
    window.__timelines["main"] = tl;
    tl.seek(0);
  });
})();
