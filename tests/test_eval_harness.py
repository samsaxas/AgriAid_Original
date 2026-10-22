import importlib.util, json, os

spec = importlib.util.spec_from_file_location("run_eval", os.path.join(os.path.dirname(__file__), "..", "eval", "run_eval.py"))
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)


def test_percentile():
    assert ev.percentile([1, 2, 3, 4, 5], 50) == 3 and ev.percentile([], 50) is None
    assert ev.percentile([1, 2, 3, 4, 5], 100) == 5


def test_hit_is_case_insensitive_any_of():
    assert ev.hit(["Early Blight (Alternaria)"], ["late blight", "alternaria"])
    assert not ev.hit(["Powdery mildew"], ["rust"])


def test_image_expect_parsing():
    assert ev.image_expect("Tomato___Early_blight") == ["early", "blight"]
    assert ev.image_expect("Corn_(maize)___Common_rust_") == ["common", "rust"]


def test_cases_file_is_wellformed():
    d = json.load(open(os.path.join(os.path.dirname(__file__), "..", "eval", "cases.json"), encoding="utf-8"))
    assert len(d["text_cases"]) == 30 and len(d["off_topic"]) == 5
    assert all(c["text"] and c["expect"] for c in d["text_cases"])
