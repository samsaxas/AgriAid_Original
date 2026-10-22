import json
import os

def load_translations():
    """Load all translation files from translations directory"""
    translations = {}
    try:
        trans_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')
        
        for file in os.listdir(trans_dir):
            if file.endswith('.json'):
                lang_code = file.split('.')[0]
                with open(os.path.join(trans_dir, file), 'r', encoding='utf-8') as f:
                    translations[lang_code] = json.load(f)
        return translations
    except Exception as e:
        raise RuntimeError(f"Error loading translations: {str(e)}")

def get_language_options(translations):
    """Generate language options for selectbox"""
    return {code: data['language_name'] for code, data in translations.items()}