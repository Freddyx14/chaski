// Chaski Devpost demo — timeline. Times come from window.DATA (build.py ← VO alignment).
(function () {
  var DATA = window.DATA, E = DATA.ev, D = E.TOTAL;
  var UI = MS.SPRINGS.ui, ST = MS.SPRINGS.settle;
  var UI_E = MS.springEase(UI.zeta), UI_D = MS.springDur(UI.zeta, UI.omega);
  var ST_E = MS.springEase(ST.zeta), ST_D = MS.springDur(ST.zeta, ST.omega);
  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function ok(v, n) { if (!isFinite(v)) throw new Error("NaN time: " + n); return v; }

  document.fonts.ready.then(function () {
    var tl = gsap.timeline({ paused: true });
    function ft(el, from, to, at) { to.immediateRender = false; return tl.fromTo(el, from, to, ok(at, el)); }
    function land(el, at) { return ft(el, { y: 200, scale: 0.5, rotation: -9, opacity: 0 }, { y: 0, scale: 1, rotation: 0, opacity: 1, duration: UI_D, ease: UI_E }, at); }
    function rise(el, at, dy) { return ft(el, { y: dy || 36, opacity: 0 }, { y: 0, opacity: 1, duration: ST_D, ease: ST_E }, at); }
    function fadeOut(el, at, d) { return ft(el, { opacity: 1 }, { opacity: 0, duration: d || 0.2, ease: "power2.in" }, at); }
    function show(el, at) { return ft(el, { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power2.out" }, at); }
    function avatar(pid, state, at) {
      $$("#ava-" + pid + " .st").forEach(function (img) {
        tl.to(img, { opacity: img.classList.contains("st-" + state) ? 1 : 0, duration: 0.18 }, ok(at, "ava"));
      });
    }
    function PS(id) { for (var i = 0; i < DATA.pages.length; i++) if (DATA.pages[i].id === id) return DATA.pages[i].start; throw new Error(id); }

    /* cards in the right column */
    var cols = {};
    $$(".card").forEach(function (c) {
      var pid = c.id.split("-")[1]; cols[pid] = cols[pid] || 0;
      c.style.top = cols[pid] + "px"; cols[pid] += c.offsetHeight + 22;
      land(c, parseFloat(c.dataset.at));
    });
    /* captions word by word */
    $$(".cap").forEach(function (cap) {
      $$(".w", cap).forEach(function (w) { ft(w, { y: 26, opacity: 0 }, { y: 0, opacity: 1, duration: 0.32, ease: ST_E }, parseFloat(w.dataset.t)); });
    });


    /* ── the globe: rotates from the Atlantic onto Peru, zooms in, pins Pilpichaca ── */
    var gc = $("#globe"), gx = gc.getContext("2d");
    var landGeo = topojson.feature(WORLD, WORLD.objects.land);
    var peru = topojson.feature(WORLD, WORLD.objects.countries).features.filter(function (f) { return f.id === "604"; })[0];
    var grat = d3.geoGraticule10();
    var PIL = [-75.08, -13.38];                    // Pilpichaca, Huancavelica (approx.)
    var proj = d3.geoOrthographic().translate([620, 620]).clipAngle(90).precision(0.3);
    var path = d3.geoPath(proj, gx);
    function ease(u) { u = Math.max(0, Math.min(1, u)); return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; }
    function drawGlobe(t) {
      var r = ease((t - 0.1) / 2.5), z = ease((t - 2.6) / 2.8);
      var lon = -20 + (PIL[0] + 20) * r, lat = 8 + (PIL[1] - 8) * r;
      var sc = 300 + 1500 * z;
      proj.rotate([-lon, -lat]).scale(sc);
      gx.clearRect(0, 0, 1240, 1240);
      gx.save(); gx.beginPath(); gx.arc(620, 620, 600, 0, 2 * Math.PI); gx.clip();
      var g = gx.createRadialGradient(520, 500, 40, 620, 620, sc * 1.05);
      g.addColorStop(0, "#2f86b8"); g.addColorStop(0.7, "#0f3d63"); g.addColorStop(1, "#081f33");
      gx.beginPath(); path({ type: "Sphere" }); gx.fillStyle = g; gx.fill();
      gx.beginPath(); path(grat); gx.strokeStyle = "rgba(255,255,255,0.10)"; gx.lineWidth = 1.5; gx.stroke();
      gx.beginPath(); path(landGeo); gx.fillStyle = "#d9c9a3"; gx.fill(); gx.strokeStyle = "rgba(24,34,31,0.35)"; gx.lineWidth = 1.2; gx.stroke();
      gx.beginPath(); path(peru); gx.fillStyle = "#f2a33a"; gx.fill(); gx.strokeStyle = "#ffffff"; gx.lineWidth = 2.5; gx.stroke();
      var hl = gx.createRadialGradient(470, 420, 10, 620, 620, sc);
      hl.addColorStop(0, "rgba(255,255,255,0.28)"); hl.addColorStop(0.5, "rgba(255,255,255,0)"); hl.addColorStop(1, "rgba(0,0,0,0.35)");
      gx.beginPath(); path({ type: "Sphere" }); gx.fillStyle = hl; gx.fill();
      gx.restore();
      gx.beginPath(); gx.arc(620, 620, Math.min(sc, 600), 0, 2 * Math.PI); gx.strokeStyle = "rgba(255,255,255,0.18)"; gx.lineWidth = 3; gx.stroke();
      var p = proj(PIL), on = t > 2.3;
      if (p && on) {
        var k = Math.max(0, Math.min(1, (t - 2.3) / 0.5)), pulse = ((t - 2.3) % 1.4) / 1.4;
        gx.beginPath(); gx.arc(p[0], p[1], 14 + 50 * pulse, 0, 2 * Math.PI); gx.strokeStyle = "rgba(224,21,122," + (0.8 * (1 - pulse) * k).toFixed(3) + ")"; gx.lineWidth = 5; gx.stroke();
        gx.beginPath(); gx.arc(p[0], p[1], 14 * k, 0, 2 * Math.PI); gx.fillStyle = "#e0157a"; gx.fill();
        gx.beginPath(); gx.arc(p[0], p[1], 6 * k, 0, 2 * Math.PI); gx.fillStyle = "#ffffff"; gx.fill();
      }
    }
    rise("#glab", 2.8, 30);
    land("#pol1", 4.6); land("#pol2", 9.2);
    /* her */
    rise("#mama-name", 1.0);
    /* why */
    land("#st1", E.w_nine); land("#st2", E.w_seven); show("#st-src", E.w_seven + 0.6);
    fadeOut(["#st1", "#st2", "#st-src"], E.w_built - 0.45, 0.25);
    land("#why-logo", E.w_built - 0.2);
    /* hands-free */
    land("#ph-hands", PS("hands") + 0.05); avatar("hands", "escuchando", E.v02 + 0.5);
    land("#d1", E.w_who); land("#d2", E.w_lang);
    /* instruction */
    land("#ph-instr", PS("instr") + 0.05); avatar("instr", "escuchando", E.v03 - 0.1);
    show("#m-es", E.v03);
    var ew = $$("#m-es .ew"), es = [].concat.apply([], DATA.caps.filter(function (c) { return c.seg === "v03"; }).map(function (c) { return c.words; }));
    ew.forEach(function (w, i) { ft(w, { opacity: 0.18 }, { opacity: 1, duration: 0.2 }, es[Math.min(i, es.length - 1)].t); });
    avatar("instr", "pensando", E.think);
    var span = E.q_b3 - E.think - 0.6;
    $$("#steps-instr .step").forEach(function (s, i) { rise(s, E.think + i * span / 3, 14); tl.set(s, { className: "step done" }, E.think + (i + 0.8) * span / 3); });
    fadeOut("#steps-instr", E.q_b3 - 0.3, 0.2);
    land("#m-qu", E.q_b3 - 0.25); avatar("instr", "hablando", E.q_b3);
    var qw = $$("#m-qu .qw"), qd = 3.2 / qw.length;
    qw.forEach(function (w, i) { ft(w, { opacity: 0.18 }, { opacity: 1, duration: 0.12 }, E.q_b3 + i * qd); });
    land("#m-ok", E.q_b3 + 3.3); avatar("instr", "reposo", E.q_b3 + 3.5);
    /* patient */
    land("#ph-pat", PS("pat") + 0.05); avatar("pat", "escuchando", E.pac);
    show("#p-qu", E.pac);
    $$("#p-wave i").forEach(function (b, i) { ft(b, { scaleY: 0.3 }, { scaleY: 1, duration: 0.18, ease: "sine.inOut", repeat: 14, yoyo: true }, E.pac + i * 0.02); });
    avatar("pat", "pensando", E.pac + 6.0);
    land("#p-es", E.pac_es); avatar("pat", "hablando", E.pac_es); avatar("pat", "reposo", E.pac_es + 2.2);
    /* ask back */
    land("#ph-ask", PS("ask") + 0.05); show("#a-es", PS("ask") + 0.4);
    land("#a-q", E.w_asks); avatar("ask", "no_entendi", E.w_asks);
    land("#a-r", E.w_repeat);
    /* emergency */
    land("#ph-emg", PS("emg") + 0.05); land("#e-grid", E.v08 + 0.6);
    ft("#eg-0", { scale: 1 }, { scale: 0.92, duration: 0.08, yoyo: true, repeat: 1 }, E.q_em - 0.45);
    fadeOut("#e-grid", E.q_em - 0.3, 0.15);
    land("#e-card", E.q_em - 0.15); avatar("emg", "hablando", E.q_em); avatar("emg", "reposo", E.q_em + 1.4);
    /* prescription */
    land("#ph-rx", PS("rx") + 0.05); land("#x-box", E.w_photo);
    land("#x-read", E.w_reads); land("#x-yes", E.w_yes); avatar("rx", "hablando", E.w_quy9);
    /* summary + loop */
    land("#ph-sum", PS("sum") + 0.05); land("#s-1", E.w_note); land("#s-2", E.w_home); land("#s-3", E.w_words);
    /* architecture */
    rise("#atag", PS("arch") + 0.3, 20);
    land("#ab0", E.v13 + 0.4); land("#ab1", E.w_ft13); show("#aw1", E.w_ft13 + 0.3);
    land("#ab5", E.w_voice13);
    land("#ab2", E.w_opus13); show("#aw2", E.w_opus13 + 0.3);
    land("#ab3", E.w_sonnet13); show("#aw3", E.w_sonnet13 + 0.3); land("#ab6", E.w_sonnet13 + 0.6); land("#ab7", E.w_sonnet13 + 1.0);
    land("#ab4", E.w_code13); show("#aw4", E.w_code13 + 0.3); show("#aw5", E.w_code13 + 0.8);
    /* numbers */
    land("#n1", E.w_184); land("#n2", E.w_54); land("#n3", E.w_2122); show("#n-src", E.w_2122 + 1.0);
    /* end */
    land("#end-logo", E.v12 - 0.1);

    var hud = $("#hud"), caps = $("#caps"), stages = $$(".stage");
    MS.drive(tl, D, function (t) {
      var dark = false;
      DATA.pages.forEach(function (p) { if (t >= p.start) dark = p.dark; });
      hud.className = dark ? "ondark" : ""; caps.className = dark ? "ondark" : "";
      if (t < DATA.pages[1].start + 0.1) drawGlobe(t);
      DATA.pages.forEach(function (p, i) {
        var k = p.id === "her" ? 1 : 1 + 0.006 * Math.max(0, Math.min(t, p.end) - p.start);
        stages[i].style.transform = "scale(" + Math.min(k, 1.06).toFixed(5) + ")";
      });
    });
    window.__timelines = window.__timelines || {};
    window.__timelines["main"] = tl;
    tl.seek(0);
  });
})();
