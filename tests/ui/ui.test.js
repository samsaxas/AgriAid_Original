// Drives the real website (HTML + app.js) against a running server using jsdom.
const { JSDOM } = require("jsdom");
const BASE = process.env.BASE || "http://127.0.0.1:8765";
let pass = 0, fail = 0;
const ok = (c, m) => { c ? pass++ : (fail++, console.log("  FAIL:", m)); console.log(c ? "  ok  " : "  --  ", m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(fn, ms = 4000) { const t = Date.now(); while (Date.now() - t < ms) { if (fn()) return true; await sleep(50); } return false; }

(async () => {
  const html = await (await fetch(BASE + "/")).text();
  const dom = new JSDOM(html, { url: BASE + "/", runScripts: "outside-only", pretendToBeVisual: true });
  const w = dom.window;
  w.fetch = (u, o) => fetch(new URL(u, BASE), o);
  w.FormData = FormData; w.Blob = Blob; w.File = File;
  w.URL.createObjectURL = () => "blob:fake"; w.URL.revokeObjectURL = () => {};
  w.HTMLMediaElement.prototype.play = () => Promise.resolve();
  w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = () => {};
  w.eval(await (await fetch(BASE + "/app.js")).text());
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  const $ = (id) => w.document.getElementById(id);
  const hidden = (id) => $(id).classList.contains("hidden");

  console.log("Languages & i18n");
  ok(await waitFor(() => $("lang").options.length === 8), "language picker has 8 options");
  $("lang").value = "hindi"; $("lang").dispatchEvent(new w.Event("change"));
  ok(await waitFor(() => $("submit").textContent.trim() === "निदान करें" || $("submit").textContent.trim() !== "Diagnose"), "switching to Hindi localizes the Diagnose button -> " + $("submit").textContent.trim());
  ok(w.localStorage.getItem("agriaid_lang") === "hindi", "language persisted in localStorage");

  console.log("Text diagnosis");
  $("submit").click();
  ok(!hidden("error"), "empty text shows validation error: " + $("error").textContent);
  $("text-input").value = "tomato leaves have yellow spots and curl";
  $("text-input").dispatchEvent(new w.Event("input"));
  ok($("counter").textContent.startsWith("40 "), "char counter updates: " + $("counter").textContent);
  $("submit").click();
  ok(await waitFor(() => !hidden("result")), "result card appears");
  ok(hidden("loading") && hidden("error"), "spinner hidden, no error");
  ok($("r-title").textContent.startsWith("[hi]"), "title translated to Hindi: " + $("r-title").textContent);
  ok($("r-remedies").children.length === 3 && $("r-prevention").children.length === 2, "3 remedies + 2 prevention items rendered");
  ok($("r-rem-label").textContent.startsWith("💊 [hi]"), "section labels localized");
  ok(hidden("r-meter") && hidden("r-contagion"), "no confidence/contagion for text input");

  console.log("Off-topic input");
  $("lang").value = "english"; $("lang").dispatchEvent(new w.Event("change")); await sleep(300);
  $("text-input").value = "who will win the politics debate";
  $("submit").click();
  ok(await waitFor(() => !hidden("error")), "off-topic shows message");
  ok($("error").classList.contains("info") && /plants or crops/.test($("error").textContent), "friendly (info) message: " + $("error").textContent);
  ok(!hidden("empty") && hidden("result"), "previous result cleared, empty state shown");

  console.log("Image diagnosis");
  w.document.querySelector('[data-tab="image"]').click();
  ok(!hidden("panel-image") && hidden("panel-text"), "photo tab switches panels");
  $("submit").click();
  ok(/photo/i.test($("error").textContent), "no photo -> prompt: " + $("error").textContent);
  const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "base64");
  const input = $("image-input");
  Object.defineProperty(input, "files", { value: [new File([png], "leaf.png", { type: "image/png" })] });
  input.dispatchEvent(new w.Event("change"));
  ok(!hidden("image-preview") && hidden("drop-hint"), "preview shown after selecting image");
  $("submit").click();
  ok(await waitFor(() => !hidden("result")), "image result appears");
  ok(!hidden("r-meter") && $("r-conf").textContent === "87%", "confidence 87% shown");
  ok(!hidden("r-contagion") && $("r-contagion").classList.contains("high"), "contagion badge = high: " + $("r-contagion").textContent);

  console.log("Voice");
  w.document.querySelector('[data-tab="audio"]').click();
  const ai = $("audio-input");
  const wav = Buffer.concat([Buffer.from("RIFF"), Buffer.alloc(40)]);
  Object.defineProperty(ai, "files", { value: [new File([wav], "note.wav", { type: "audio/wav" })] });
  ai.dispatchEvent(new w.Event("change"));
  ok($("audio-name").textContent === "note.wav", "audio file accepted");
  $("submit").click();
  ok(await waitFor(() => !hidden("r-transcript")), "transcript shown for voice input");
  ok(/tomato leaves/.test($("r-transcript").textContent), "transcript: " + $("r-transcript").textContent);

  console.log("Listen");
  $("listen").click();
  ok(await waitFor(() => !hidden("player")), "audio player revealed after Listen");

  console.log("Security");
  const js = await (await fetch(BASE + "/app.js")).text();
  ok(!/\.innerHTML\s*=\s*[^"'\s]/.test(js.replace(/innerHTML = ""/g, "")), "no innerHTML assignment with dynamic content");

  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
