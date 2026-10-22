import json
import os

import pytest
from gtts.lang import tts_langs
from deep_translator import GoogleTranslator as RealTranslator

from app import pipeline, speech, translation
from conftest import IMAGE_ANSWER, TEXT_ANSWER


# ---------- parsing ----------
def test_parse_text_answer():
    s = pipeline.parse_sections(TEXT_ANSWER)
    assert s["diagnosis"] == ["Early blight (Alternaria solani)", "Nitrogen deficiency"]
    assert len(s["remedies"]) == 3 and len(s["prevention"]) == 2
    assert s["confidence"] is None and s["contagion"] is None


def test_parse_image_answer_with_confidence_and_contagion():
    s = pipeline.parse_sections(IMAGE_ANSWER)
    assert s["diagnosis"][0].startswith("Late blight")
    assert s["confidence"] == 87
    assert s["contagion_level"] == "high"


def test_parse_handles_markdown_bold_and_bullets():
    txt = "🩺 Diagnosis:\n- **Powdery mildew**\n- Poor airflow\n💊 Remedies:\n- Spray sulfur\n🌱 Prevention:\n- Space plants"
    s = pipeline.parse_sections(txt)
    assert s["diagnosis"] == ["Powdery mildew", "Poor airflow"]
    assert s["remedies"] == ["Spray sulfur"]


def test_parse_garbage_gives_empty_diagnosis():
    assert pipeline.parse_sections("hello world")["diagnosis"] == []


def test_confidence_capped_at_100():
    assert pipeline.parse_sections("🩺 Diagnosis: x\n📊 Confidence: 250%")["confidence"] == 100


# ---------- speech cleaning ----------
SAMPLES = {
    "hindi": "निदान: टमाटर के पत्तों पर पीले धब्बे",
    "tamil": "நோய் கண்டறிதல்: தக்காளி இலைகளில் மஞ்சள் புள்ளிகள்",
    "kannada": "ರೋಗನಿರ್ಣಯ: ಟೊಮೇಟೊ ಎಲೆಗಳ ಮೇಲೆ ಹಳದಿ ಕಲೆಗಳು",
    "telugu": "టమాటా ఆకులపై పసుపు మచ్చలు",
    "bengali": "টমেটো পাতায় হলুদ দাগ",
    "gu": "ટામેટાના પાંદડા પર પીળા ડાઘ",
    "punjabi": "ਟਮਾਟਰ ਦੇ ਪੱਤਿਆਂ ਉੱਤੇ ਪੀਲੇ ਧੱਬੇ",
}


@pytest.mark.parametrize("lang,text", SAMPLES.items())
def test_clean_text_preserves_indic_scripts(lang, text):
    cleaned = speech.clean_text_for_speech("🩺 " + text + " ✅ **ok**")
    assert text.replace(":", "") in cleaned.replace(":", "")  # words intact (vowel signs kept)
    assert "🩺" not in cleaned and "*" not in cleaned


def test_clean_text_symbols():
    assert speech.clean_text_for_speech("Use 50% neem/soap & water") == "Use 50 percent neem or soap and water"


# ---------- language config ----------
def test_every_translation_file_has_language_mapping():
    files = {f[:-5] for f in os.listdir(translation.TRANSLATIONS_DIR) if f.endswith(".json")}
    assert files == set(translation.LANGS)


def test_translation_files_have_identical_keys():
    tr = translation.load_translations()
    base = set(tr["english"]["strings"])
    for code, d in tr.items():
        assert set(d["strings"]) == base, code
        assert len(d["instructions"]) == len(tr["english"]["instructions"]), code


@pytest.mark.parametrize("lang", list(translation.LANGS))
def test_codes_supported_by_gtts_and_translator(lang):
    assert translation.tts_code(lang) in tts_langs()
    RealTranslator(source="en", target=translation.tr_code(lang))  # raises if unsupported


def test_translate_to_english_passthrough_and_empty():
    assert translation.translate_to_english("My tomato leaves have yellow spots and curl") == \
        "My tomato leaves have yellow spots and curl"
    assert translation.translate_to_english("   ") == ""


def test_translate_batch_falls_back_to_english():
    from conftest import FakeTranslator
    FakeTranslator.fail = True
    out, ok = translation.translate_batch(["a", "b"], "hindi")
    assert out == ["a", "b"] and ok is False
