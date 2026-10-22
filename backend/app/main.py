"""AgriAid API (FastAPI). Serves the JSON API under /api and the website from /frontend."""
import logging
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config, gemini, pipeline, speech, translation

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agriaid")

MAX_TEXT_CHARS = 2000
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_AUDIO_BYTES = 12 * 1024 * 1024
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

app = FastAPI(title="AgriAid API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _lang(lang):
    if lang not in translation.LANGS:
        raise HTTPException(422, f"Unsupported language '{lang}'.")
    return lang


def _run(fn, *args):
    """Run a pipeline function and map domain errors to clean HTTP errors."""
    try:
        return fn(*args)
    except config.MissingAPIKeyError as e:
        raise HTTPException(503, str(e))
    except gemini.NotAgriculturalError as e:
        raise HTTPException(422, {"code": "not_agricultural", "message": str(e)})
    except (gemini.GeminiError, translation.TranslationError, speech.SpeechError) as e:
        log.warning("Request failed: %s", e)
        raise HTTPException(502, str(e))


async def _read(file: UploadFile, limit: int, what: str):
    data = await file.read(limit + 1)
    if not data:
        raise HTTPException(422, f"The {what} file is empty.")
    if len(data) > limit:
        raise HTTPException(413, f"The {what} file is too large (max {limit // (1024 * 1024)} MB).")
    return data


class TextRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=MAX_TEXT_CHARS)
    lang: str = "english"


class RetranslateRequest(BaseModel):
    english: str = Field(..., min_length=1, max_length=12000)
    transcript: str | None = None
    lang: str = "english"


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=6000)
    lang: str = "english"


@app.get("/api/health")
def health():
    return {"status": "ok", "model": config.get_model(), "api_key_configured": config.has_api_key()}


@app.get("/api/languages")
def languages():
    return translation.language_list()


@app.get("/api/translations/{lang}")
def ui_strings(lang: str):
    try:
        return translation.language_payload(_lang(lang))
    except ValueError:
        raise HTTPException(404, "Unknown language.")
    except translation.TranslationError as e:
        log.warning("UI translation failed for %s: %s", lang, e)
        raise HTTPException(502, str(e))


@app.post("/api/diagnose/text")
def diagnose_text(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(422, "Please describe the crop issue.")
    return _run(pipeline.diagnose_text, req.text, _lang(req.lang))


@app.post("/api/diagnose/image")
async def diagnose_image(file: UploadFile = File(...), lang: str = Form("english")):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(415, "Please upload a JPG, PNG or WEBP image.")
    data = await _read(file, MAX_IMAGE_BYTES, "image")
    return _run(pipeline.diagnose_image, data, _lang(lang))


@app.post("/api/diagnose/audio")
async def diagnose_audio(file: UploadFile = File(...), lang: str = Form("english")):
    data = await _read(file, MAX_AUDIO_BYTES, "audio")
    return _run(pipeline.diagnose_audio, data, file.content_type, _lang(lang))


@app.post("/api/translate-result")
def translate_result(req: RetranslateRequest):
    return _run(pipeline.translate_existing_result, req.english, _lang(req.lang), req.transcript)


@app.post("/api/speak")
def speak(req: SpeakRequest):
    audio = _run(speech.generate_speech, req.text, _lang(req.lang))
    return Response(audio, media_type="audio/mpeg")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
