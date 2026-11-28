#!/usr/bin/env python3
"""Import BECE Mathematics practice questions from scraped Nyansapo year pages.

Source: https://nyansapo.academy/bece/mathematics/<year> (public year pages;
Next.js flight payload holds question, options, answer, explanation, topic).

Usage:
  python3 import_maths.py --source-dir DIR --bank FILE [--dry-run]

Only self-contained, text-only questions with a published answer and a worked
explanation are imported. Diagram/chart/table questions are skipped because the
site has no figures; empty answers and very short explanations are skipped too.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

TOPIC_MAP = {
    "Numbers & Number Sense": "numbers",
    "Number Bases": "number-bases",
    "Fractions, Decimals & Percentages": "fractions-decimals",
    "Ratio & Proportion": "fractions-decimals",
    "Commercial Maths (Profit, Loss, Tax, Interest)": "fractions-decimals",
    "Indices & Logarithms": "indices",
    "Sequences & Patterns": "algebra",
    "Algebraic Expressions": "algebra",
    "Quadratic Equations": "algebra",
    "Linear Equations & Inequalities": "equations",
    "Triangles & Polygons": "geometry",
    "Angles & Lines": "geometry",
    "Coordinate Geometry & Graphs": "geometry",
    "Transformations & Matrices": "geometry",
    "Vectors": "geometry",
    "Circles": "geometry",
    "Constructions & Loci": "geometry",
    "Perimeter & Area": "mensuration",
    "Volume & Surface Area": "mensuration",
    "Trigonometry": "trigonometry",
    "Statistics: Data Collection & Averages": "statistics",
    "Statistics: Charts, Tables & Graphs": "statistics",
    "Probability": "statistics",
    "Sets": "sets",
}

VISUAL = re.compile(
    r"\b(diagram|figure|chart|graph|table|mapping|magic square|shaded|pictogram|scale drawing|below|above)\b",
    re.I,
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def dedupe_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", norm(text).lower())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True, type=Path)
    ap.add_argument("--bank", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bank = json.loads(args.bank.read_text())
    seen = {dedupe_key(q["prompt"]) for q in bank}
    ids = {q["id"] for q in bank}
    added = []
    skipped = Counter()

    for path in sorted(args.source_dir.glob("*.json")):
        year = int(path.stem)
        for obj in json.loads(path.read_text()):
            for q in obj["questions"]:
                prompt = norm(q.get("question"))
                explanation = norm(q.get("explanation"))
                answer = norm(q.get("answer")).upper()
                opts = q.get("options") or {}
                topic = TOPIC_MAP.get(q.get("topic"))
                if not topic:
                    skipped["unknown topic"] += 1
                    continue
                if not answer or answer not in "ABCD" or len(answer) != 1:
                    skipped["no answer"] += 1
                    continue
                if len(prompt) < 15 or len(prompt) > 600:
                    skipped["bad prompt"] += 1
                    continue
                if VISUAL.search(prompt):
                    skipped["needs figure"] += 1
                    continue
                if len(explanation) < 40:
                    skipped["thin explanation"] += 1
                    continue
                if any(not norm(opts.get(k)) for k in "ABCD"):
                    skipped["missing option"] += 1
                    continue
                if any(re.search(r"\{\{|\}\}|\(\(|\)\)", norm(opts[k])) for k in "ABCD"):
                    skipped["malformed option"] += 1
                    continue
                key = dedupe_key(prompt)
                if key in seen:
                    skipped["duplicate"] += 1
                    continue
                seen.add(key)
                prefix = topic[:4].replace("-", "") or "m"
                idx = 1
                while f"m-{prefix}-{year}-{idx:02d}" in ids:
                    idx += 1
                qid = f"m-{prefix}-{year}-{idx:02d}"
                ids.add(qid)
                added.append({
                    "id": qid,
                    "subject": "mathematics",
                    "year": year,
                    "paper": 1,
                    "topic": topic,
                    "prompt": prompt,
                    "options": [norm(opts[k]) for k in "ABCD"],
                    "answerIndex": "ABCD".index(answer),
                    "explanation": explanation,
                })

    print(f"existing={len(bank)} added={len(added)} skipped={dict(skipped)}")
    print("topics:", dict(Counter(q["topic"] for q in added)))
    print("years:", min(q["year"] for q in added), "-", max(q["year"] for q in added))
    if args.dry_run:
        for q in added[:5]:
            print(json.dumps(q, ensure_ascii=False)[:500])
        return
    merged = bank + added
    args.bank.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {len(merged)} questions to {args.bank}")


if __name__ == "__main__":
    main()
