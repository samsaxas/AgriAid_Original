import pytest

from app import translation
from conftest import make_png, make_wav


def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["api_key_configured"] is True


def test_languages_and_ui_strings(client):
    langs = client.get("/api/languages").json()
    assert len(langs) == 8 and {"code": "english", "name": "English"} in langs
    assert "diagnose" in client.get("/api/translations/hindi").json()["strings"]
    assert client.get("/api/translations/klingon").status_code == 404


@pytest.mark.parametrize("lang", list(translation.LANGS))
def test_text_diagnosis_all_languages(client, lang):
    r = client.post("/api/diagnose/text", json={"text": "tomato leaves have yellow spots", "lang": lang})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["language"] == lang and d["translated"] is True
    assert len(d["diagnosis"]) == 2 and len(d["remedies"]) == 3 and len(d["prevention"]) == 2
    code = translation.tr_code(lang)
    if code != "en":
        assert d["diagnosis"][0].startswith(f"[{code}]") and d["labels"]["remedies"].startswith(f"[{code}]")


def test_non_english_input_is_translated_before_analysis(client, monkeypatch):
    seen = {}
    from app import gemini
    orig = gemini.analyze_text
    monkeypatch.setattr(gemini, "analyze_text", lambda t: seen.setdefault("t", t) and orig(t))
    client.post("/api/diagnose/text", json={"text": "टमाटर के पत्तों पर पीले धब्बे हैं और वे मुरझा रहे हैं", "lang": "hindi"})
    assert seen["t"].startswith("[en] ")  # was routed through translator to English


def test_text_validation(client):
    assert client.post("/api/diagnose/text", json={"text": "  ", "lang": "english"}).status_code == 422
    assert client.post("/api/diagnose/text", json={"text": "ab", "lang": "english"}).status_code == 422
    assert client.post("/api/diagnose/text", json={"text": "x" * 2001, "lang": "english"}).status_code == 422
    assert client.post("/api/diagnose/text", json={"text": "tomato blight", "lang": "klingon"}).status_code == 422


def test_off_topic_is_rejected_cleanly(client):
    r = client.post("/api/diagnose/text", json={"text": "who will win the politics debate tonight", "lang": "english"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "not_agricultural"


def test_translation_outage_falls_back_to_english(client):
    from conftest import FakeTranslator
    FakeTranslator.fail = True
    d = client.post("/api/diagnose/text", json={"text": "tomato leaves have yellow spots", "lang": "tamil"}).json()
    assert d["translated"] is False and d["diagnosis"][0].startswith("Early blight")


def test_image_diagnosis(client):
    r = client.post("/api/diagnose/image", files={"file": ("leaf.png", make_png(), "image/png")}, data={"lang": "hindi"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["confidence"] == 87 and d["contagion_level"] == "high"


def test_image_rejections(client):
    assert client.post("/api/diagnose/image", files={"file": ("a.txt", b"hi", "text/plain")}).status_code == 415
    assert client.post("/api/diagnose/image", files={"file": ("a.png", b"", "image/png")}).status_code == 422
    assert client.post("/api/diagnose/image", files={"file": ("a.png", b"notanimage", "image/png")}).status_code == 502
    big = b"\x89PNG" + b"0" * (8 * 1024 * 1024 + 10)
    assert client.post("/api/diagnose/image", files={"file": ("a.png", big, "image/png")}).status_code == 413


def test_large_image_is_downscaled():
    from app import gemini
    data, mime = gemini.prepare_image(make_png((4000, 3000)))
    from PIL import Image
    import io
    assert max(Image.open(io.BytesIO(data)).size) <= gemini.MAX_IMAGE_SIDE and mime == "image/jpeg"


def test_audio_diagnosis_returns_transcript(client):
    r = client.post("/api/diagnose/audio", files={"file": ("v.wav", make_wav(), "audio/wav")}, data={"lang": "telugu"})
    assert r.status_code == 200, r.text
    assert r.json()["transcript"] == "tomato leaves have yellow spots"


def test_audio_unsupported_format(client):
    r = client.post("/api/diagnose/audio", files={"file": ("v.webm", b"junkdata", "audio/webm")})
    assert r.status_code == 502 and "Unsupported audio" in r.json()["detail"]


def test_speak(client):
    r = client.post("/api/speak", json={"text": "🩺 निदान: पीले धब्बे", "lang": "hindi"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and len(r.content) > 100


def test_speak_rejects_symbol_only_text(client):
    assert client.post("/api/speak", json={"text": "🩺💊", "lang": "english"}).status_code == 502


def test_missing_api_key_gives_503(client, monkeypatch):
    from app import gemini
    monkeypatch.undo()  # drop fake _generate
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    gemini._client = None
    r = client.post("/api/diagnose/text", json={"text": "tomato leaves yellow", "lang": "english"})
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["detail"]


def test_frontend_is_served(client):
    html = client.get("/").text
    assert "AgriAid" in html and 'id="diagnose"' in html
    assert client.get("/app.js").status_code == 200 and client.get("/styles.css").status_code == 200
