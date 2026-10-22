#!/usr/bin/env python3
"""Live evaluation of the AgriAid pipeline (needs GEMINI_API_KEY and internet).

  python eval/run_eval.py                      # 30 symptom cases + 5 off-topic prompts (English)
  python eval/run_eval.py --lang hindi         # same cases, translated to Hindi first (full multilingual path)
  python eval/run_eval.py --images data/PlantVillage   # folders named like Tomato___Early_blight
  python eval/run_eval.py --delay 4            # pause between calls (free-tier rate limits)

Prints a markdown table and writes eval/results/<timestamp>.json. Nothing here is mocked.
"""
import argparse, json, os, statistics, sys, time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))


def percentile(values, p):
    if not values:
        return None
    v = sorted(values)
    k = (len(v) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def hit(diagnosis_items, expect):
    blob = " ".join(diagnosis_items).lower()
    return any(k.lower() in blob for k in expect)


def format_ok(result):
    return bool(result["diagnosis"]) and len(result["remedies"]) >= 2 and len(result["prevention"]) >= 1


def image_expect(folder):
    """'Tomato___Early_blight' -> ['early','blight'] (all words must appear); 'healthy' -> ['healthy']."""
    disease = folder.split("___")[-1].replace("_", " ").lower()
    words = [w for w in disease.replace("(", " ").replace(")", " ").split() if len(w) > 2]
    return words


def english_of(result):
    return result["english"]


def run(args):
    from app import gemini, pipeline, translation

    cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
    report = {"timestamp": datetime.now().isoformat(timespec="seconds"), "model": os.getenv("GEMINI_MODEL") or "default",
              "language": args.lang, "errors": []}
    lat, hits, fmts, n_err = [], 0, 0, 0
    tc = cases["text_cases"][: args.limit] if args.limit else cases["text_cases"]

    for i, c in enumerate(tc, 1):
        text = c["text"]
        if args.lang != "english":  # simulate a farmer writing in their own language
            text = translation.translate_batch([text], args.lang)[0][0]
        t0 = time.time()
        try:
            res = pipeline.diagnose_text(text, args.lang)
            dt = time.time() - t0
            # judge on the ENGLISH answer so keywords are comparable across languages
            eng = pipeline.parse_sections(res["english"])["diagnosis"]
            ok = hit(eng, c["expect"])
            hits += ok; fmts += format_ok(res); lat.append(dt)
            print(f"[{i:02d}/{len(tc)}] {'HIT ' if ok else 'MISS'} {dt:5.1f}s  {c['crop']:8s} -> {eng[:1]}")
        except Exception as e:
            n_err += 1; report["errors"].append({"case": i, "error": str(e)})
            print(f"[{i:02d}/{len(tc)}] ERR  {e}")
        time.sleep(args.delay)

    n = len(tc)
    ok_n = n - n_err
    report["text"] = {"cases": n, "errors": n_err, "top3_hit_rate": hits / ok_n if ok_n else None,
                      "format_compliance": fmts / ok_n if ok_n else None,
                      "latency_p50_s": percentile(lat, 50), "latency_p95_s": percentile(lat, 95)}

    rej = 0
    off = cases["off_topic"]
    for q in off:
        try:
            pipeline.diagnose_text(q, "english")
        except gemini.NotAgriculturalError:
            rej += 1
        except Exception as e:
            report["errors"].append({"off_topic": q, "error": str(e)})
        time.sleep(args.delay)
    report["off_topic"] = {"prompts": len(off), "rejected": rej, "rejection_rate": rej / len(off)}

    if args.images:
        ih, it, ilat, ierr = 0, 0, [], 0
        for folder in sorted(os.listdir(args.images)):
            d = os.path.join(args.images, folder)
            if not os.path.isdir(d):
                continue
            words = image_expect(folder)
            files = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png")))[: args.per_class]
            for f in files:
                t0 = time.time()
                try:
                    res = pipeline.diagnose_image(open(os.path.join(d, f), "rb").read(), "english")
                    eng = " ".join(pipeline.parse_sections(res["english"])["diagnosis"]).lower()
                    ih += all(w in eng for w in words); it += 1; ilat.append(time.time() - t0)
                except Exception as e:
                    ierr += 1; report["errors"].append({"image": f"{folder}/{f}", "error": str(e)})
                time.sleep(args.delay)
        report["image"] = {"images": it, "errors": ierr, "accuracy": ih / it if it else None,
                           "latency_p50_s": percentile(ilat, 50), "latency_p95_s": percentile(ilat, 95)}

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{args.lang}.json")
    json.dump(report, open(out, "w"), indent=2)
    print_table(report); print(f"\nSaved {out}")


def pct(x): return "n/a" if x is None else f"{x * 100:.1f}%"
def sec(x): return "n/a" if x is None else f"{x:.1f}s"


def print_table(r):
    t, o = r["text"], r["off_topic"]
    print(f"\n| Metric ({r['language']}) | Result |\n|---|---|")
    print(f"| Symptom cases (text) | {t['cases']} ({t['errors']} errors) |")
    print(f"| Diagnosis hit rate (expected condition in answer) | {pct(t['top3_hit_rate'])} |")
    print(f"| Output format compliance | {pct(t['format_compliance'])} |")
    print(f"| Latency p50 / p95 | {sec(t['latency_p50_s'])} / {sec(t['latency_p95_s'])} |")
    print(f"| Off-topic rejection | {o['rejected']}/{o['prompts']} ({pct(o['rejection_rate'])}) |")
    if "image" in r:
        i = r["image"]
        print(f"| Image accuracy ({i['images']} images) | {pct(i['accuracy'])} |")
        print(f"| Image latency p50 / p95 | {sec(i['latency_p50_s'])} / {sec(i['latency_p95_s'])} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="english")
    ap.add_argument("--images")
    ap.add_argument("--per-class", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=2.0)
    run(ap.parse_args())
