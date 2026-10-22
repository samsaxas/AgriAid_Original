import os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
from app import config
from google import genai
from google.genai import types

client = genai.Client(api_key=config.get_api_key(), http_options=types.HttpOptions(timeout=30_000))
models = [config.get_model()] + ([os.getenv("GEMINI_FALLBACK_MODEL")] if os.getenv("GEMINI_FALLBACK_MODEL") else [])
for m in models:
    t0 = time.time()
    try:
        r = client.models.generate_content(model=m, contents="Reply with the single word: ok")
        print(f"OK    {m:28s} {time.time() - t0:5.1f}s  -> {r.text.strip()[:40]!r}")
    except Exception as e:
        print(f"FAIL  {m:28s} {time.time() - t0:5.1f}s  -> {str(e)[:150]}")