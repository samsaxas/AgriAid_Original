(() => {
  "use strict";
  const API = (document.querySelector('meta[name="api-base"]') || {}).content || "";
  const $ = (id) => document.getElementById(id);
  const EXAMPLES = [
    "Tomato leaves have dark rings and yellowing at the bottom",
    "White powder on squash leaves",
    "Wheat leaves with orange-brown spots",
    "Rice leaves with diamond-shaped grey spots",
  ];
  const state = { lang: localStorage.getItem("agriaid_lang") || "english", tab: "text",
                  image: null, audio: null, result: null, ui: {}, busy: false, speechUrl: null, languageRequest: 0 };

  /* ---------- helpers ---------- */
  const show = (el, on = true) => el.classList.toggle("hidden", !on);
  function showError(msg, info = false) {
    const el = $("error"); el.textContent = msg; el.classList.toggle("info", info); show(el, !!msg);
  }
  async function api(path, opts = {}) {
    let res;
    try { res = await fetch(API + path, opts); }
    catch { throw new Error("Cannot reach the server. Check your connection and try again."); }
    if (!res.ok) {
      let msg = `Request failed (${res.status}).`, code = null;
      try {
        const body = await res.json(); const d = body.detail;
        if (typeof d === "string") msg = d;
        else if (d && d.message) { msg = d.message; code = d.code; }
        else if (Array.isArray(d)) msg = "Please check your input and try again.";
      } catch {}
      const err = new Error(msg); err.code = code; throw err;
    }
    return res;
  }

  /* ---------- i18n ---------- */
  function tr(key, fallback) { return state.ui[key] || fallback || key; }
  function applyUI(strings) {
    state.ui = strings || {};
    document.documentElement.lang = state.lang === "gu" ? "gu" : state.lang.slice(0, 2);
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const value = state.ui[el.dataset.i18n];
      if (value) el.textContent = value;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const value = state.ui[el.dataset.i18nPlaceholder];
      if (value) el.placeholder = value;
    });
    const resultLabels = state.result && state.result.labels;
    if (resultLabels) {
      $("r-label").textContent = resultLabels.diagnosis;
      $("r-rem-label").textContent = "💊 " + resultLabels.remedies;
      $("r-prev-label").textContent = "🌱 " + resultLabels.prevention;
      if (state.result.confidence != null) $("r-conf-label").textContent = resultLabels.confidence;
      if (state.result.contagion) $("r-contagion").textContent = `${resultLabels.contagion}: ${state.result.contagion}`;
    }
    if (state.audio && $("audio-name").dataset.filename) $("audio-name").textContent = $("audio-name").dataset.filename;
  }
  async function setLang(code) {
    const requestId = ++state.languageRequest;
    const previous = state.lang;
    state.lang = code;
    localStorage.setItem("agriaid_lang", code);
    $("lang").value = code;
    try {
      const response = await api(`/api/translations/${code}`);
      const payload = await response.json();
      // Ignore a slower response if the user selected another language meanwhile.
      if (requestId !== state.languageRequest) return;
      if (!payload.translation_complete) throw new Error("The interface translation is incomplete.");
      applyUI(payload.strings || {});
      if (state.result && state.result.english) {
        try {
          const response = await api("/api/translate-result", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ english: state.result.english, transcript: state.result.transcript, lang: code })
          });
          const translated = await response.json();
          if (requestId === state.languageRequest) render(translated);
        } catch (error) {
          if (requestId === state.languageRequest) showError("The page language changed, but the existing diagnosis could not be translated. Retry the language change or run the diagnosis again.");
        }
      }
    } catch (error) {
      if (requestId === state.languageRequest) {
        state.lang = previous;
        $("lang").value = previous;
        showError("Could not load this language. Please check the server/API connection and try again.");
      }
    }
  }

  async function initLanguages() {
    let langs = [{ code: "english", name: "English" }];
    try { langs = await (await api("/api/languages")).json(); } catch {}
    const sel = $("lang"); sel.innerHTML = "";
    langs.forEach((l) => sel.append(new Option(l.name, l.code)));
    if (!langs.some((l) => l.code === state.lang)) state.lang = "english";
    sel.onchange = () => setLang(sel.value);
    await setLang(state.lang);
  }

  /* ---------- tabs ---------- */
  function setTab(tab) {
    state.tab = tab; showError("");
    document.querySelectorAll(".tab").forEach((b) => {
      const on = b.dataset.tab === tab; b.classList.toggle("active", on); b.setAttribute("aria-selected", on);
    });
    ["text", "image", "audio"].forEach((t) => show($("panel-" + t), t === tab));
  }

  /* ---------- text ---------- */
  function initText() {
    const ta = $("text-input");
    ta.addEventListener("input", () => ($("counter").textContent = `${ta.value.length} / 2000`));
    EXAMPLES.forEach((t) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.textContent = t.split(" ").slice(0, 3).join(" ") + "…";
      b.title = t; b.onclick = () => { ta.value = t; ta.dispatchEvent(new Event("input")); };
      $("examples").append(b);
    });
  }

  /* ---------- image ---------- */
  function setImage(file) {
    if (!file) return;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return showError("Please choose a JPG, PNG or WEBP image.");
    if (file.size > 8 * 1024 * 1024) return showError("That image is larger than 8 MB.");
    showError(""); state.image = file;
    const img = $("image-preview"); img.src = URL.createObjectURL(file); show(img); show($("drop-hint"), false);
  }
  function initImage() {
    const dz = $("dropzone");
    $("image-input").onchange = (e) => setImage(e.target.files[0]);
    ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
    ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
    dz.addEventListener("drop", (e) => setImage(e.dataTransfer.files[0]));
  }

  /* ---------- audio (record -> 16 kHz mono WAV, because Gemini does not accept browser webm) ---------- */
  function encodeWav(samples, rate) {
    const buf = new ArrayBuffer(44 + samples.length * 2), v = new DataView(buf);
    const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
    w(0, "RIFF"); v.setUint32(4, 36 + samples.length * 2, true); w(8, "WAVEfmt ");
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    w(36, "data"); v.setUint32(40, samples.length * 2, true);
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i])); v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([buf], { type: "audio/wav" });
  }
  async function blobToWav(blob) {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const decoded = await ctx.decodeAudioData(await blob.arrayBuffer()); ctx.close();
    const rate = 16000, off = new OfflineAudioContext(1, Math.ceil(decoded.duration * rate), rate);
    const src = off.createBufferSource(); src.buffer = decoded; src.connect(off.destination); src.start();
    return encodeWav((await off.startRendering()).getChannelData(0), rate);
  }
  function setAudio(blob, name) {
    state.audio = blob; const p = $("audio-preview");
    p.src = URL.createObjectURL(blob); show(p); $("audio-name").dataset.filename = name || ""; $("audio-name").textContent = name || "";
  }
  function initAudio() {
    let rec = null, chunks = [], timer = null, t0 = 0;
    const btn = $("rec-btn");
    const stopTimer = () => { clearInterval(timer); };
    btn.onclick = async () => {
      showError("");
      if (rec && rec.state === "recording") { rec.stop(); return; }
      if (!navigator.mediaDevices || !window.MediaRecorder)
        return showError(tr("error_recording", "Recording is not supported in this browser. Please upload an audio file instead."));
      let stream;
      try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
      catch { return showError(tr("error_mic", "Microphone access was blocked. Allow it in your browser or upload an audio file.")); }
      chunks = []; rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      rec.onstop = async () => {
        stopTimer(); stream.getTracks().forEach((t) => t.stop());
        btn.classList.remove("on"); $("rec-status").textContent = tr("click_to_record", "Click to record");
        try { setAudio(await blobToWav(new Blob(chunks, { type: rec.mimeType })), tr("recorded", "Recorded voice note")); }
        catch { showError(tr("error_audio_process", "Could not process the recording. Please try again or upload a file.")); }
      };
      rec.start(); btn.classList.add("on"); $("rec-status").textContent = tr("recording", "Recording… click to stop"); t0 = Date.now();
      timer = setInterval(() => {
        const s = Math.floor((Date.now() - t0) / 1000);
        $("rec-time").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
        if (s >= 90) rec.stop();
      }, 250);
    };
    $("audio-input").onchange = (e) => {
      const f = e.target.files[0]; if (!f) return;
      if (f.size > 12 * 1024 * 1024) return showError("That audio file is larger than 12 MB.");
      setAudio(f, f.name);
    };
  }

  /* ---------- diagnose ---------- */
  function setBusy(on) {
    state.busy = on; $("submit").disabled = on;
    show($("loading"), on); if (on) { show($("empty"), false); show($("result"), false); }
  }
  async function submit() {
    if (state.busy) return; showError("");
    let req;
    if (state.tab === "text") {
      const text = $("text-input").value.trim();
      if (text.length < 3) return showError(tr("warning", "Please describe the crop issue"));
      req = api("/api/diagnose/text", { method: "POST", headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ text, lang: state.lang }) });
    } else {
      const file = state.tab === "image" ? state.image : state.audio;
      if (!file) return showError(state.tab === "image" ? tr("error_photo", "Please choose a photo first.") : tr("error_voice", "Please record or upload audio first."));
      const fd = new FormData();
      fd.append("file", file, file.name || (state.tab === "image" ? "photo.jpg" : "voice.wav")); fd.append("lang", state.lang);
      req = api(`/api/diagnose/${state.tab}`, { method: "POST", body: fd });
    }
    setBusy(true);
    try { render(await (await req).json()); }
    catch (e) {
      show($("empty"), true); showError(e.message, e.code === "not_agricultural");
    } finally { setBusy(false); }
  }

  /* ---------- render result (textContent only: no HTML injection) ---------- */
  function fill(ol, items) { ol.innerHTML = ""; items.forEach((t) => { const li = document.createElement("li"); li.textContent = t; ol.append(li); }); }
  function render(r) {
    state.result = r; const L = r.labels;
    if (state.speechUrl) { URL.revokeObjectURL(state.speechUrl); state.speechUrl = null; }
    show($("player"), false); $("player").removeAttribute("src");
    $("r-label").textContent = L.diagnosis;
    $("r-title").textContent = r.diagnosis[0] || "";
    fill($("r-diagnosis"), r.diagnosis.slice(1));
    $("r-rem-label").textContent = "💊 " + L.remedies; fill($("r-remedies"), r.remedies);
    $("r-prev-label").textContent = "🌱 " + L.prevention; fill($("r-prevention"), r.prevention);
    show($("r-meter"), r.confidence != null);
    if (r.confidence != null) {
      $("r-conf-label").textContent = L.confidence; $("r-conf").textContent = r.confidence + "%";
      requestAnimationFrame(() => ($("r-conf-bar").style.width = r.confidence + "%"));
    }
    const c = $("r-contagion"); show(c, !!r.contagion);
    if (r.contagion) { c.textContent = `${L.contagion}: ${r.contagion}`; c.className = "badge" + (r.contagion_level === "high" ? " high" : r.contagion_level === "medium" ? " med" : ""); }
    const transcriptEl = $("r-transcript"); show(transcriptEl, !!r.transcript); transcriptEl.textContent = r.transcript ? "“" + r.transcript + "”" : "";
    show($("r-untranslated"), r.translated === false);
    if (r.translated === false) $("r-untranslated").textContent = tr("error_translation", "Translation was unavailable, so this answer is shown in English.");
    show($("result"), true);
    if (window.innerWidth < 900) $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function plainText() {
    const r = state.result, L = r.labels;
    return [r.diagnosis.join("\n"), `\n${L.remedies}:`, ...r.remedies.map((x, i) => `${i + 1}. ${x}`),
            `\n${L.prevention}:`, ...r.prevention.map((x, i) => `${i + 1}. ${x}`)].join("\n");
  }
  async function listen() {
    const btn = $("listen"), r = state.result; if (!r) return;
    const text = [r.diagnosis[0], ...r.diagnosis.slice(1), `${r.labels.remedies}.`, ...r.remedies, `${r.labels.prevention}.`, ...r.prevention].join(". ");
    btn.disabled = true; const old = btn.textContent; btn.textContent = "⏳ …";
    try {
      const blob = await (await api("/api/speak", { method: "POST", headers: { "Content-Type": "application/json" },
                                                    body: JSON.stringify({ text, lang: r.language }) })).blob();
      state.speechUrl = URL.createObjectURL(blob);
      const p = $("player"); p.src = state.speechUrl; show(p); p.play().catch(() => {});
    } catch (e) { showError(tr("error_audio_unavailable", "Audio is unavailable right now: ") + e.message); }
    finally { btn.disabled = false; btn.textContent = old; }
  }

  /* ---------- init ---------- */
  document.addEventListener("DOMContentLoaded", async () => {
    $("year").textContent = new Date().getFullYear();
    document.querySelectorAll(".tab").forEach((b) => (b.onclick = () => setTab(b.dataset.tab)));
    initText(); initImage(); initAudio();
    $("submit").onclick = submit; $("listen").onclick = listen; $("print").onclick = () => window.print();
    $("copy").onclick = async () => {
      try { await navigator.clipboard.writeText(plainText()); $("copy").textContent = tr("copied", "✅ Copied"); setTimeout(() => ($("copy").textContent = tr("copy", "📋 Copy")), 1500); } catch {}
    };
    await initLanguages();
  });
})();
