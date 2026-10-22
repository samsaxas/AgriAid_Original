"""Text-to-speech (gTTS) and audio helpers."""
import io
import re
import unicodedata

from gtts import gTTS
from gtts.lang import tts_langs

from app.translation import tts_code


class SpeechError(RuntimeError):
    pass


def clean_text_for_speech(text):
    """Make text TTS-friendly without damaging non-Latin scripts.

    Keeps letters, combining marks (Indic vowel signs), digits, whitespace and basic
    punctuation; drops emoji and markdown symbols.
    """
    text = text.replace("&", " and ").replace("%", " percent ").replace("/", " or ")
    kept = [
        ch if (unicodedata.category(ch)[0] in "LMN" or ch.isspace() or ch in ".,;:!?") else " "
        for ch in text
    ]
    text = "".join(kept)
    text = re.sub(r"\s*\n\s*", ". ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def generate_speech(text, lang="english"):
    """Return MP3 bytes for text spoken in the selected language."""
    cleaned = clean_text_for_speech(text or "")
    if not cleaned:
        raise SpeechError("Nothing to speak.")
    code = tts_code(lang)
    if code not in tts_langs():
        code = "en"
    try:
        buf = io.BytesIO()
        gTTS(text=cleaned, lang=code).write_to_fp(buf)
    except Exception as e:
        raise SpeechError(f"Text-to-speech failed: {e}") from e
    data = buf.getvalue()
    if len(data) < 100:
        raise SpeechError("Text-to-speech returned no audio.")
    return data


GEMINI_AUDIO_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/mp3",
    "audio/ogg", "audio/flac", "audio/aac", "audio/aiff",
}


def normalize_audio(data, mime):
    """Return (bytes, mime) Gemini accepts; converts other formats (webm/mp4) via ffmpeg if present."""
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in GEMINI_AUDIO_TYPES:
        return data, ("audio/wav" if mime in ("audio/x-wav", "audio/wave") else mime)
    try:
        from pydub import AudioSegment

        seg = AudioSegment.from_file(io.BytesIO(data))
        out = io.BytesIO()
        seg.set_channels(1).set_frame_rate(16000).export(out, format="wav")
        return out.getvalue(), "audio/wav"
    except Exception as e:
        raise SpeechError(
            f"Unsupported audio format '{mime or 'unknown'}'. Use wav/mp3/ogg/flac (or install ffmpeg): {e}"
        ) from e
