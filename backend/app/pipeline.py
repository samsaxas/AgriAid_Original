"""Orchestration: farmer input -> language-aware Gemini -> structured result.

JSON is the preferred Gemini response format. The text-heading parser remains
as a compatibility fallback for older responses and mocked test responses.
"""
import json
import re

from app import gemini, translation


# English headings retained for compatibility with older Gemini responses.
HEADERS = {
    "diagnosis": r"(?:🩺\s*)?Diagnosis\s*:",
    "confidence": r"(?:📊\s*)?Confidence\s*:",
    "remedies": r"(?:💊\s*)?Remedies\s*:",
    "prevention": r"(?:🌱\s*)?Prevention\s*:",
    "contagion": r"(?:⚠️?\s*)?Contagion\s*:",
}

# Localized heading aliases are a fallback only. JSON output is preferred.
HEADER_ALIASES = {
    "diagnosis": [
        "निदान", "રોગ નિદાન", "રોગનું નિદાન", "రోగ నిర్ధారణ", "నిర్ధారణ",
        "ರೋಗ ನಿರ್ಣಯ", "ರೋಗನಿರ್ಣಯ", "நோய் கண்டறிதல்", "நோய்",
        "ਨਿਦਾਨ", "রোগ নির্ণয়",
    ],
    "remedies": [
        "उपचार", "उपाय", "ઉપાયો", "ઉપચાર", "పరిష్కారాలు", "చికిత్స",
        "ಪರಿಹಾರಗಳು", "ಚಿಕಿತ್ಸೆ", "தீர்வுகள்", "சிகிச்சை",
        "ਉਪਚਾਰ", "ਉਪਾਅ", "প্রতিকার", "চিকিৎসা",
    ],
    "prevention": [
        "रोकथाम", "બચાવ", "નિવારણ", "నివారణ", "నిరోధం",
        "ತಡೆಗಟ್ಟುವಿಕೆ", "ತಡೆಗಟ್ಟುವ ಕ್ರಮಗಳು", "தடுப்பு",
        "ਰੋਕਥਾਮ", "প্রতিরোধ",
    ],
    "confidence": [
        "विश्वास स्तर", "વિશ્વાસ સ્તર", "నమ్మక స్థాయి",
        "ವಿಶ್ವಾಸದ ಮಟ್ಟ", "நம்பிக்கை நிலை", "ਭਰੋਸੇ ਦਾ ਪੱਧਰ", "আস্থার মাত্রা",
    ],
    "contagion": [
        "संक्रमण", "ચેપ", "వ్యాప్తి", "ಸೋಂಕು", "பரவல்",
        "ਫੈਲਾਅ", "সংক্রমণ",
    ],
}

_HEADER_PATTERNS = []
for _key, _pattern in HEADERS.items():
    _HEADER_PATTERNS.append((_key, re.compile(_pattern, re.IGNORECASE)))

for _key, _aliases in HEADER_ALIASES.items():
    for _alias in _aliases:
        _HEADER_PATTERNS.append((
            _key,
            re.compile(r"(?:" + re.escape(_alias) + r")\s*[:：]", re.IGNORECASE),
        ))


def _clean(value):
    if value is None:
        return ""
    value = str(value).replace("**", "").replace("__", "").replace("*", "")
    return re.sub(r"\s+", " ", value).strip(" -•\t\r\n")


def _to_items(value):
    """Convert JSON arrays or formatted text into a clean list of strings."""
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            if isinstance(item, (dict, list)):
                item = json.dumps(item, ensure_ascii=False)
            cleaned = _clean(item)
            if cleaned:
                result.append(cleaned)
        return result

    if isinstance(value, dict):
        return [_clean(json.dumps(value, ensure_ascii=False))]

    text = str(value).strip()
    if not text:
        return []

    # Split numbered/bulleted lists while preserving non-English characters.
    chunks = re.split(
        r"(?:^|\n)\s*(?:\d+\s*[.)、]|[-•▪])\s*",
        text,
    )
    chunks = [_clean(chunk) for chunk in chunks if _clean(chunk)]

    if len(chunks) <= 1:
        # Some model responses put numbered items on one line.
        inline_chunks = re.split(r"\s+\d+\s*[.)]\s*", text)
        if len(inline_chunks) > 1:
            chunks = [_clean(chunk) for chunk in inline_chunks if _clean(chunk)]

    return chunks or [_clean(text)]


def _extract_json(text):
    """Extract a JSON object, including one wrapped in Markdown fences."""
    candidate = (text or "").strip()
    if not candidate:
        return None

    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s*```$", "", candidate)

    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass

    # Recover the first complete JSON object from surrounding explanatory text.
    start = candidate.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(candidate)):
        char = candidate[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(candidate[start:index + 1])
                    return parsed if isinstance(parsed, dict) else None
                except json.JSONDecodeError:
                    return None
    return None


def _from_json(data):
    status = str(data.get("status", "ok")).strip().lower()
    if status in {"not_agricultural", "not agricultural", "out_of_scope"}:
        raise gemini.NotAgriculturalError(
            "The input does not appear to be about plants or crops."
        )

    # Accept a few common alternate field names from older/model-generated JSON.
    diagnosis = data.get("diagnosis", data.get("disease", data.get("cause")))
    remedies = data.get("remedies", data.get("treatment", data.get("treatments")))
    prevention = data.get("prevention", data.get("preventive_measures"))
    confidence = data.get("confidence", data.get("confidence_score"))
    contagion = data.get("contagion", data.get("spread_risk"))

    if isinstance(diagnosis, dict):
        diagnosis = diagnosis.get("items", diagnosis.get("text", diagnosis.get("description")))

    if isinstance(remedies, dict):
        remedies = remedies.get("items", remedies.get("text", remedies.get("steps")))

    if isinstance(prevention, dict):
        prevention = prevention.get("items", prevention.get("text", prevention.get("steps")))

    if isinstance(confidence, str):
        match = re.search(r"\d{1,3}", confidence)
        confidence = int(match.group()) if match else None

    try:
        confidence = int(confidence) if confidence is not None else None
        if confidence is not None:
            confidence = max(0, min(100, confidence))
    except (TypeError, ValueError):
        confidence = None

    contagion_text = _clean(contagion) if contagion is not None else None
    contagion_level = None
    if contagion_text:
        level_match = re.search(
            r"\b(low|medium|moderate|high)\b",
            contagion_text,
            flags=re.IGNORECASE,
        )
        if level_match:
            contagion_level = {
                "moderate": "medium"
            }.get(level_match.group(1).lower(), level_match.group(1).lower())

    return {
        "diagnosis": _to_items(diagnosis),
        "remedies": _to_items(remedies),
        "prevention": _to_items(prevention),
        "confidence": confidence,
        "contagion": contagion_text,
        "contagion_level": contagion_level,
    }


def _parse_heading_response(text):
    """Compatibility parser for the previous emoji + English-heading format."""
    matches = []
    for key, pattern in _HEADER_PATTERNS:
        for match in pattern.finditer(text or ""):
            matches.append((match.start(), match.end(), key))

    matches.sort(key=lambda item: item[0])
    raw = {}

    for index, (start, end, key) in enumerate(matches):
        stop = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        raw.setdefault(key, text[end:stop])

    diagnosis = _to_items(raw.get("diagnosis"))
    remedies = _to_items(raw.get("remedies"))
    prevention = _to_items(raw.get("prevention"))

    confidence_match = re.search(r"(\d{1,3})\s*%", raw.get("confidence", ""))
    confidence = int(confidence_match.group(1)) if confidence_match else None
    if confidence is not None:
        confidence = min(confidence, 100)

    contagion = _clean(raw.get("contagion")) or None
    contagion_level = None
    if contagion:
        level_match = re.search(
            r"\b(low|medium|moderate|high)\b",
            contagion,
            flags=re.IGNORECASE,
        )
        if level_match:
            contagion_level = {
                "moderate": "medium"
            }.get(level_match.group(1).lower(), level_match.group(1).lower())

    return {
        "diagnosis": diagnosis,
        "remedies": remedies,
        "prevention": prevention,
        "confidence": confidence,
        "contagion": contagion,
        "contagion_level": contagion_level,
    }


def parse_sections(text):
    """Parse JSON first, then fall back to the legacy heading format."""
    if not text or not str(text).strip():
        return {
            "diagnosis": [],
            "remedies": [],
            "prevention": [],
            "confidence": None,
            "contagion": None,
            "contagion_level": None,
        }

    parsed_json = _extract_json(text)
    if parsed_json is not None:
        return _from_json(parsed_json)

    if str(text).strip().upper().startswith(gemini.NOT_AGRICULTURAL):
        raise gemini.NotAgriculturalError(
            "The input does not appear to be about plants or crops."
        )

    return _parse_heading_response(str(text))


def _get_labels(lang):
    """Use the project's translated labels, with safe defaults if unavailable."""
    translated_labels = getattr(translation, "translated_labels", None)
    if callable(translated_labels):
        try:
            return translated_labels(lang)
        except Exception:
            # Diagnosis content should not fail because a display-label lookup fails.
            pass

    return {
        "diagnosis": "Diagnosis",
        "remedies": "Remedies",
        "prevention": "Prevention",
        "confidence": "Confidence",
        "contagion": "Contagion",
    }


def _build_result(model_text, lang, transcript=None):
    sections = parse_sections(model_text)

    if not sections["diagnosis"]:
        raise gemini.GeminiError(
            "Gemini returned a response, but no diagnosis could be extracted. "
            "Please try again."
        )

    return {
        "diagnosis": sections["diagnosis"],
        "remedies": sections["remedies"],
        "prevention": sections["prevention"],
        "contagion": sections["contagion"],
        "contagion_level": sections["contagion_level"],
        "language": lang,
        "translated": True,
        "confidence": sections["confidence"],
        "labels": _get_labels(lang),
        "transcript": transcript,
        # Kept for compatibility with existing frontend/API consumers.
        # This is the raw Gemini response, in the requested language.
        "english": model_text,
    }


def diagnose_text(text, lang):
    return _build_result(gemini.analyze_text(text, lang), lang)


def diagnose_image(image_bytes, lang):
    return _build_result(gemini.analyze_image(image_bytes, lang), lang)


def diagnose_audio(audio_bytes, mime, lang):
    from app.speech import normalize_audio

    data, normalized_mime = normalize_audio(audio_bytes, mime)
    transcript = gemini.transcribe_audio(data, normalized_mime)
    diagnosis = gemini.analyze_text(transcript, lang)
    return _build_result(diagnosis, lang, transcript=transcript)
