import io
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import gemini as _gemini  # noqa: E402

REAL_GENERATE = _gemini._generate  # un-faked, for the retry tests

TEXT_ANSWER = """🩺 Diagnosis:
1. Early blight (Alternaria solani)
2. Nitrogen deficiency
💊 Remedies:
1. Remove infected lower leaves.
2. Spray copper-based fungicide weekly.
3. Mulch to stop soil splash.
🌱 Prevention:
1. Rotate crops every 2-3 years.
2. Water at the base, not on leaves."""

IMAGE_ANSWER = """🩺 Diagnosis: Late blight (Phytophthora infestans)
1. Dark water-soaked lesions on leaves
2. White mould on the underside
📊 Confidence: 87%
💊 Remedies:
1. Remove and destroy infected plants.
2. Apply a mancozeb fungicide.
🌱 Prevention:
1. Use resistant varieties.
2. Avoid overhead irrigation.
⚠️ Contagion: High - spreads fast in humid weather"""


class FakeTranslator:
    """Stands in for deep_translator.GoogleTranslator (no network in tests)."""
    fail = False

    def __init__(self, source="auto", target="en"):
        self.target = target

    def translate(self, text):
        if FakeTranslator.fail:
            raise RuntimeError("translate down")
        return f"[{self.target}] {text}"

    def translate_batch(self, items):
        if FakeTranslator.fail:
            raise RuntimeError("translate down")
        return [f"[{self.target}] {t}" for t in items]


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    from app import gemini, speech, translation

    FakeTranslator.fail = False
    translation.translated_labels.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_FALLBACK_MODEL", raising=False)  # keep tests independent of a local .env
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(translation, "GoogleTranslator", FakeTranslator)

    calls = []

    def fake_generate(contents, temperature=0.2, retries=2):
        prompt = contents[0]
        calls.append(prompt[:20])
        if prompt.startswith("Transcribe"):
            return "tomato leaves have yellow spots"
        if "politics" in prompt:
            return "NOT_AGRICULTURAL"
        if prompt.startswith("You are an agricultural expert. Analyze this crop photo"):
            return IMAGE_ANSWER
        return TEXT_ANSWER

    monkeypatch.setattr(gemini, "_generate", fake_generate)

    def fake_tts(self, fp):
        fp.write(b"ID3" + b"\x00" * 500)

    monkeypatch.setattr(speech.gTTS, "write_to_fp", fake_tts)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def make_png(size=(64, 64), color=(30, 140, 40)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def make_wav(seconds=1, rate=16000):
    import struct
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<h", 0) * rate * seconds)
    return buf.getvalue()
