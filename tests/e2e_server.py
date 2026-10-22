"""Run the real server with only external Google calls faked (for offline E2E/UI tests)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["GEMINI_API_KEY"] = "test"
import uvicorn
from app import gemini, speech, translation
from conftest import FakeTranslator, TEXT_ANSWER, IMAGE_ANSWER

translation.GoogleTranslator = FakeTranslator
speech.gTTS.write_to_fp = lambda self, fp: fp.write(b"ID3" + b"\0" * 500)
def fake(contents, temperature=0.2, retries=2):
    p = contents[0]
    if p.startswith("Transcribe"): return "tomato leaves have yellow spots"
    if "politics" in p: return "NOT_AGRICULTURAL"
    return IMAGE_ANSWER if "crop photo" in p else TEXT_ANSWER
gemini._generate = fake
from app.main import app
uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
