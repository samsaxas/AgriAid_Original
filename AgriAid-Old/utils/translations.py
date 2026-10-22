from googletrans import Translator

# Map your language codes to googletrans codes
LANG_CODE_MAP = {
    'gu': 'Gujarati',
    'hi': 'Hindi',
    'bn': 'Bengali',
    'pa': 'Punjabi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'kn': 'Kannada'
}

def translate_from_english(text, target_lang):
    """Translate English text to target language"""
    try:
        translator = Translator()
        # Convert your language code to googletrans code
        dest_code = LANG_CODE_MAP.get(target_lang.lower(), 'en')
        translated = translator.translate(text, dest=dest_code)
        return translated.text
    except Exception as e:
        raise RuntimeError(f"Translation failed: {str(e)}")