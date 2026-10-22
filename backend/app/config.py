"""Configuration: API key + model name, read lazily from the environment / .env.

Nothing is hardcoded. A missing key raises MissingAPIKeyError only when a Gemini call
is actually made, so the server still starts and reports the problem via /api/health.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Gemini 1.5 and 2.0 Flash are shut down. Override with GEMINI_MODEL if Google retires this:
# https://ai.google.dev/gemini-api/docs/deprecations
DEFAULT_MODEL = "gemini-3.8-flash"


class MissingAPIKeyError(RuntimeError):
    pass


def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise MissingAPIKeyError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return key


def get_model():
    return os.getenv("GEMINI_MODEL") or DEFAULT_MODEL


def has_api_key():
    return bool(os.getenv("GEMINI_API_KEY"))
