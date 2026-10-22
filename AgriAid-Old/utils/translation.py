from langdetect import detect
from deep_translator import GoogleTranslator

def translate_to_english(text):
    detected_lang = detect(text)
    if detected_lang != 'en':
        return GoogleTranslator(source=detected_lang, target='en').translate(text)
    return text

def translate_from_english(text, target_lang):
    return GoogleTranslator(source='en', target=target_lang).translate(text)
