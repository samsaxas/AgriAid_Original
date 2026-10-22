# import pytest
# from google.genai import errors

# from app import gemini
# from conftest import REAL_GENERATE


# class _Resp:
#     def __init__(self, text): self.text = text


# def _client(side_effects):
#     calls = {"n": 0}

#     class M:
#         def generate_content(self, **kw):
#             e = side_effects[min(calls["n"], len(side_effects) - 1)]
#             calls["n"] += 1
#             if isinstance(e, Exception):
#                 raise e
#             return _Resp(e)

#     class C:
#         models = M()

#     return C(), calls


# def _api_err(code):
#     return errors.APIError(code, {"error": {"message": "x", "status": "S"}})


# @pytest.fixture(autouse=True)
# def nosleep(monkeypatch):
#     monkeypatch.setattr(gemini.time, "sleep", lambda s: None)


# def test_retries_transient_then_succeeds(monkeypatch):
#     c, calls = _client([_api_err(503), _api_err(429), "ok"])
#     monkeypatch.setattr(gemini, "_get_client", lambda: c)
#     assert REAL_GENERATE(["hi"]) == "ok" and calls["n"] == 3


# def test_does_not_retry_client_errors(monkeypatch):
#     c, calls = _client([_api_err(404)])
#     monkeypatch.setattr(gemini, "_get_client", lambda: c)
#     with pytest.raises(gemini.GeminiError):
#         REAL_GENERATE(["hi"])
#     assert calls["n"] == 1


# def test_empty_response_is_an_error(monkeypatch):
#     c, _ = _client(["", "", ""])
#     monkeypatch.setattr(gemini, "_get_client", lambda: c)
#     with pytest.raises(gemini.GeminiError):
#         REAL_GENERATE(["hi"])



import pytest
from google.genai import errors

from app import gemini
from conftest import REAL_GENERATE


class _Resp:
    def __init__(self, text): self.text = text


def _client(side_effects):
    calls = {"n": 0}

    class M:
        def generate_content(self, **kw):
            e = side_effects[min(calls["n"], len(side_effects) - 1)]
            calls["n"] += 1
            if isinstance(e, Exception):
                raise e
            return _Resp(e)

    class C:
        models = M()

    return C(), calls


def _api_err(code):
    return errors.APIError(code, {"error": {"message": "x", "status": "S"}})


@pytest.fixture(autouse=True)
def nosleep(monkeypatch):
    monkeypatch.setattr(gemini.time, "sleep", lambda s: None)


def test_retries_transient_then_succeeds(monkeypatch):
    c, calls = _client([_api_err(503), _api_err(429), "ok"])
    monkeypatch.setattr(gemini, "_get_client", lambda: c)
    assert REAL_GENERATE(["hi"]) == "ok" and calls["n"] == 3


def test_does_not_retry_client_errors(monkeypatch):
    c, calls = _client([_api_err(404)])
    monkeypatch.setattr(gemini, "_get_client", lambda: c)
    with pytest.raises(gemini.GeminiError):
        REAL_GENERATE(["hi"])
    assert calls["n"] == 1


def test_empty_response_is_an_error(monkeypatch):
    c, _ = _client(["", "", ""])
    monkeypatch.setattr(gemini, "_get_client", lambda: c)
    with pytest.raises(gemini.GeminiError):
        REAL_GENERATE(["hi"])


def test_falls_back_to_second_model_when_first_keeps_failing(monkeypatch):
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "fallback-model")
    used = []

    class M:
        def generate_content(self, **kw):
            used.append(kw["model"])
            if kw["model"] != "fallback-model":
                raise _api_err(503)
            return _Resp("from fallback")

    class C:
        models = M()

    monkeypatch.setattr(gemini, "_get_client", lambda: C())
    assert REAL_GENERATE(["hi"], retries=1) == "from fallback"
    assert used == [gemini.get_model()] * 2 + ["fallback-model"]


def test_users_see_friendly_message_not_raw_api_error(monkeypatch):
    c, _ = _client([_api_err(503)])
    monkeypatch.setattr(gemini, "_get_client", lambda: c)
    with pytest.raises(gemini.GeminiError) as ei:
        REAL_GENERATE(["hi"])
    msg = str(ei.value)
    assert "busy" in msg.lower() and "503" not in msg and "UNAVAILABLE" not in msg