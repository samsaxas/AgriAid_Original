"""Gemini API wrapper for AgriAid.

Diagnosis responses are requested as JSON so the pipeline does not depend on
Gemini reproducing exact headings, emoji, or Markdown formatting.
"""
import io
import json
import logging
import time

from PIL import Image, UnidentifiedImageError

from app.config import MissingAPIKeyError, get_api_key, get_model

logger = logging.getLogger(__name__)

NOT_AGRICULTURAL = "NOT_AGRICULTURAL"
MAX_IMAGE_SIDE = 1600
_client = None

LANGUAGE_NAMES = {
    "english": "English",
    "hindi": "Hindi",
    "telugu": "Telugu",
    "tamil": "Tamil",
    "kannada": "Kannada",
    "punjabi": "Punjabi",
    "bengali": "Bengali",
    "gu": "Gujarati",
    "gujarati": "Gujarati",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
    "pa": "Punjabi",
    "bn": "Bengali",
    "hi": "Hindi",
    "en": "English",
}


class GeminiError(RuntimeError):
    """Raised when the Gemini call fails or returns unusable content."""


class NotAgriculturalError(ValueError):
    """Raised when the input is not about plants, crops, soil, pests or farming."""


def normalize_language(lang):
    """Return a supported language name; accepts common language codes too."""
    key = str(lang or "english").strip().lower()
    if key not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported output language: {lang}")
    return LANGUAGE_NAMES[key]


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=get_api_key())
    return _client


def _generate(contents, temperature=0.2, retries=2, json_mode=False):
    """Call Gemini with bounded retries for transient API/network failures."""
    from google.genai import errors, types

    config_args = {"temperature": temperature}
    if json_mode:
        config_args["response_mime_type"] = "application/json"

    config = types.GenerateContentConfig(**config_args)
    last_error = None

    for attempt in range(retries + 1):
        try:
            response = _get_client().models.generate_content(
                model=get_model(),
                contents=contents,
                config=config,
            )
            response_text = (getattr(response, "text", None) or "").strip()
            if not response_text:
                raise GeminiError("Gemini returned an empty response.")
            return response_text

        except MissingAPIKeyError:
            raise
        except GeminiError as exc:
            last_error = exc
        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            last_error = GeminiError(
                f"Gemini API error ({code if code is not None else 'unknown'}): {exc}"
            )
            # Quota exhaustion is not normally fixed by retrying immediately.
            if code == 429:
                break
            if code not in (500, 502, 503, 504):
                break
        except Exception as exc:
            last_error = GeminiError(f"Gemini request failed: {exc}")

        if attempt < retries:
            time.sleep(min(1.5 * (2 ** attempt), 6))

    logger.error("Gemini generation failed: %s", last_error)
    raise last_error or GeminiError("Gemini request failed.")


def _diagnosis_prompt(language, task, input_text=None):
    language_name = normalize_language(language)
    context = (
        f'Farmer description: """{input_text.strip()}"""'
        if input_text else
        "Analyze the attached crop/leaf photograph."
    )

    return f"""
You are an experienced agricultural crop-diagnosis assistant.
{context}

Write every human-readable value in the JSON response in {language_name}.
Do not write diagnosis, symptoms, remedies, prevention advice, confidence
explanations, or contagion descriptions in English unless the selected
language is English. Keep scientific and Latin species names unchanged.
Use clear, practical language suitable for an Indian farmer.

If the input is not about plants, crops, leaves, soil, pests, plant diseases,
or farming, return exactly this JSON object:
{{"status":"not_agricultural"}}

Otherwise return ONLY one valid JSON object. Do not use Markdown fences,
comments, introductory text, or text after the JSON.

Required JSON structure:
{{
  "status": "ok",
  "diagnosis": ["Most likely cause and explanation", "Other possible cause if relevant"],
  "confidence": 85,
  "remedies": ["Specific actionable treatment step 1", "Specific actionable treatment step 2"],
  "prevention": ["Specific prevention step 1", "Specific prevention step 2"],
  "contagion": "Medium"
}}

Rules:
- diagnosis, remedies and prevention must always be JSON arrays of strings.
- Give 1-3 concise diagnosis items and 2-5 practical remedies/prevention items.
- For image diagnosis, describe only symptoms visible in the photograph; do not
  claim certainty beyond the evidence.
- For text diagnosis, distinguish likely causes from confirmed diagnoses.
- confidence must be an integer from 0 to 100, or null if it cannot be estimated.
- contagion must be a short {language_name} description or null when not applicable.
- Do not invent chemical dosages. Advise following the product label and local
  agricultural guidance where pesticide use is suggested.
- The task is: {task}.
""".strip()


def analyze_text(input_text, lang="english"):
    """Diagnose a farmer's text description in the selected language."""
    if not input_text or not input_text.strip():
        raise ValueError("Empty description.")

    prompt = _diagnosis_prompt(
        lang,
        task="diagnose the issue described by the farmer",
        input_text=input_text,
    )
    return _generate([prompt], json_mode=True)


def prepare_image(image_bytes):
    """Validate and downscale an uploaded image. Returns (jpeg_bytes, mime_type)."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise GeminiError(f"Could not read the image: {exc}") from exc

    image = image.convert("RGB")
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90)
    return output.getvalue(), "image/jpeg"


def analyze_image(image_bytes, lang="english"):
    """Diagnose a crop disease from image bytes in the selected language."""
    from google.genai import types

    if not image_bytes:
        raise GeminiError("No image data was provided.")

    data, mime_type = prepare_image(image_bytes)
    image_part = types.Part.from_bytes(data=data, mime_type=mime_type)
    prompt = _diagnosis_prompt(
        lang,
        task="diagnose the plant or crop shown in the photograph",
    )
    return _generate([prompt, image_part], json_mode=True)


TRANSCRIBE_PROMPT = (
    "Transcribe this audio recording word for word. The speaker is a farmer "
    "describing a plant, crop, pest or soil problem, possibly in an Indian "
    "language. Return only the transcript in the original spoken language, "
    "with no commentary."
)


def transcribe_audio(audio_bytes, mime_type="audio/wav"):
    """Transcribe a spoken description in its original spoken language."""
    from google.genai import types

    if not audio_bytes:
        raise GeminiError("No audio data was provided.")

    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    transcript = _generate(
        [TRANSCRIBE_PROMPT, audio_part],
        temperature=0.0,
        json_mode=False,
    )
    if len(transcript.strip()) < 3:
        raise GeminiError("Could not understand the audio.")
    return transcript.strip()
