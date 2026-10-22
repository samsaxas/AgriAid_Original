# Resume description — AgriAid

**Short (1–2 lines):**
AgriAid | FastAPI, Gemini, JavaScript — Full-stack multilingual crop-disease diagnosis web app (text, photo, voice input; 8 Indian languages + audio answers). 80 automated tests (93% backend coverage).

**Bullets (use after running `python eval/run_eval.py` and filling the XX values):**
- Built a full-stack web app (FastAPI backend, responsive vanilla-JS frontend) that diagnoses crop diseases from text, photos or voice in 8 languages and reads advice aloud, using Google Gemini for analysis and speech transcription.
- Designed an API-first pipeline (language detection → translation → LLM → structured parsing → section-wise translation → TTS) with input validation, retry/backoff, off-topic guardrails and graceful fallbacks when translation or audio services fail.
- Evaluated on 30 labelled symptom cases: **XX% diagnosis hit rate (English), XX% via Hindi input**, XX% output-format compliance, XX/5 off-topic prompts rejected, p50 latency X.Xs.
- Wrote 80 automated tests (55 pytest + 25 browser-level UI tests) with 93% backend coverage; found and fixed production-breaking issues (retired Gemini model, exposed API key, broken Indic-script TTS).

(Only quote the XX numbers after you have run the evaluation yourself.)
