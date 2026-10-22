# 🌱 AgriAid — Multilingual Crop Disease Diagnosis

AgriAid helps farmers diagnose crop problems and get treatment and prevention advice **in their own language**. Describe the problem in text, upload a photo of the affected plant, or record a voice note, and AgriAid returns likely causes, remedies and prevention steps, and can read them aloud.

It is a full-stack web app: a **FastAPI** backend (Google Gemini for analysis) and a standalone, responsive **website** frontend (plain HTML/CSS/JavaScript, no build step).

## Features
- **3 input modes:** text, photo (JPG/PNG/WEBP), voice (record in-browser or upload wav/mp3/ogg/flac/aac)
- **8 languages:** English, Hindi, Telugu, Tamil, Kannada, Punjabi, Bengali, Gujarati (input in any language is auto-detected and translated; output is translated back, section by section)
- **Structured results:** primary diagnosis, confidence meter and contagion risk (photo mode), numbered remedies and prevention steps
- **Audio answers** in the selected language (gTTS), plus copy and print
- **Guardrails:** off-topic questions are rejected politely, uploads are validated and size-limited, images are downscaled, transient API errors are retried, translation outages fall back to English

## Architecture
```
Browser (frontend/: index.html, styles.css, app.js)
   │  JSON / multipart over HTTP
   ▼
FastAPI (backend/app/main.py)  ──►  pipeline.py ──►  gemini.py      (analyze text / image, transcribe audio)
                                          │      └►  translation.py (detect, translate, language maps)
                                          └──────►   speech.py      (gTTS, audio normalisation)
```

| Endpoint | Purpose |
|---|---|
| `POST /api/diagnose/text` | `{text, lang}` → structured diagnosis |
| `POST /api/diagnose/image` | multipart `file`, `lang` |
| `POST /api/diagnose/audio` | multipart `file`, `lang` (returns the transcript too) |
| `POST /api/speak` | `{text, lang}` → `audio/mpeg` |
| `GET /api/languages`, `/api/translations/{lang}`, `/api/health` | metadata |

Interactive API docs are at `/docs` when the server is running.

## Quick start
```bash
git clone <this repo> && cd AgriAid
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env                                      # then put your GEMINI_API_KEY in .env
cd backend && uvicorn app.main:app --reload               # open http://localhost:8000
```
Or with Docker: `docker build -t agriaid . && docker run -p 8000:8000 --env-file .env agriaid`

Get a free Gemini key at <https://aistudio.google.com/apikey>. **Never commit `.env`.**
The default model is `gemini-3.8-flash`; set `GEMINI_MODEL` to change it (older `gemini-1.5-*` and `gemini-2.0-*` models are shut down).

## Testing & metrics

```bash
pip install -r backend/requirements-dev.txt
python -m pytest --cov=backend/app                        # backend: unit + API tests
python tests/e2e_server.py &  (cd tests/ui && npm install && node ui.test.js)   # website UI tests
```

### Automated tests (measured)
| | Result |
|---|---|
| Backend tests (pytest: parsing, language mapping, TTS cleaning, API, retries, eval harness) | **55 passing** |
| Backend line coverage | **93%** |
| Website UI tests (real `app.js` driven in jsdom against the running server: language switch, text/photo/voice flows, validation, off-topic, results rendering, Listen) | **25 passing** |
| All 8 languages × text flow verified through the real API | 8 / 8 |
| App-side overhead per request (200 requests, external APIs stubbed) | p50 **4.0 ms**, p95 **7.1 ms** |

External services (Gemini, Google Translate, gTTS) are stubbed in these tests, so they verify *the application's* behaviour, not model quality.

### Model-quality evaluation (live)
`eval/run_eval.py` runs 30 labelled symptom descriptions (tomato, potato, rice, wheat, maize, chilli, brinjal, cabbage…) through the real pipeline, plus 5 off-topic prompts. Expected conditions are author-labelled; a case passes if the expected disease appears in the diagnosis.

```bash
python eval/run_eval.py                       # English, text
python eval/run_eval.py --lang hindi          # translates the cases first: tests the full multilingual path
python eval/run_eval.py --images data/PlantVillage --per-class 5   # optional photo accuracy (folders like Tomato___Early_blight)
```
Results are printed as a markdown table and saved in `eval/results/`.

#### Latest live evaluation result

Run: **22 October 2026** · Model: `gemini-3.5-flash-lite` · Language: English · Input: 30 labelled text cases and 5 off-topic prompts.

| Metric | Measured result |
|---|---:|
| Labelled cases completed | 30 / 30 |
| Top-3 diagnosis hit rate | **96.67%** (29 / 30) |
| Output-format compliance | **100%** |
| Median latency (p50) | **7.40 seconds** |
| 95th-percentile latency (p95) | **51.10 seconds** |
| Off-topic prompts rejected | **5 / 5 (100%)** |
| Evaluation errors | **0** |

The hit-rate metric is **top-3**, not top-1: the expected condition appeared among the model's first three suggested diagnoses. These figures are from one live run and are not a guarantee of field accuracy. Latency includes external model/API time and can vary with service load. Hindi evaluation has not yet been run for this result set; do not interpret the English metrics as multilingual model-quality measurements.

Raw machine-readable output: [`eval_english_results.json`](eval_english_results.json).


## Project structure
```
backend/app/   main.py (API) · pipeline.py · gemini.py · translation.py · speech.py · config.py
frontend/      index.html · styles.css · app.js
translations/  UI strings per language (JSON)
tests/         pytest suite · e2e_server.py · ui/ (jsdom)
eval/          run_eval.py · cases.json
```

## Screenshots

The screenshots below show the final interface and example diagnosis outputs. The UI language is selected from the language dropdown; these examples show Hindi and Kannada.

| Hindi — homepage | How it works |
|---|---|
| ![AgriAid Hindi homepage](docs/screenshots/hindi-homepage.png) | ![AgriAid how it works section](docs/screenshots/how-it-works.png) |

| Hindi — photo diagnosis | Kannada — photo diagnosis |
|---|---|
| ![AgriAid Hindi photo diagnosis result](docs/screenshots/hindi-photo-diagnosis.png) | ![AgriAid Kannada photo diagnosis result](docs/screenshots/kannada-photo-diagnosis.png) |

## Notes & limitations
- Diagnoses are AI suggestions; accuracy depends on input quality. For severe or widespread outbreaks, consult a local agronomist.
- Uploaded photos/audio are processed in memory and sent to Google's APIs; AgriAid does not store them.
- Translation and speech use free Google endpoints (deep-translator, gTTS) and can be rate-limited; the app degrades gracefully (English text, no audio).
- Page chrome (marketing sections) is English; the diagnosis tool UI and all results are localised.
