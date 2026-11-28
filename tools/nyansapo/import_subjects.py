#!/usr/bin/env python3
"""Import BECE practice questions for all subjects from Nyansapo year pages.

Source: https://nyansapo.academy/bece/<subject>/<year> — the public page embeds
question, options, answer, explanation and topic in its Next.js flight payload.
Scrape those pages to a directory of <subject>_<year>.json files first.

Questions whose source topic is comprehension/cloze are skipped because the
passage is not part of the bank. Figure-dependent prompts are skipped too.
Where the source has no worked solution, the published answer key is quoted
as the explanation instead of inventing working.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

# source topic -> (our subject slug, our topic slug)
TOPIC_MAP = {
    # English
    "Grammar: Parts of Speech": ("english", "eng-grammar"),
    "Grammar: Sentence Structure & Types": ("english", "eng-grammar"),
    "Grammar: Tenses & Aspect": ("english", "eng-grammar"),
    "Grammar: Concord (Subject-Verb Agreement)": ("english", "eng-grammar"),
    "Vocabulary in Context": ("english", "eng-vocabulary"),
    "Idioms & Fixed Expressions": ("english", "eng-vocabulary"),
    "Figurative Language & Literary Devices": ("english", "eng-vocabulary"),
    "Word Choice, Register & Style": ("english", "eng-vocabulary"),
    "Grammar: Punctuation & Spelling": ("english", "eng-spelling"),
    "Oral English": ("english", "eng-oral"),
    # Science
    "Matter, States & Particle Theory": ("integrated-science", "sci-matter"),
    "Mixtures & Separation Techniques": ("integrated-science", "sci-matter"),
    "Atoms, Elements & Compounds": ("integrated-science", "sci-matter"),
    "Chemical Reactions": ("integrated-science", "sci-chemical-changes"),
    "Acids, Bases & Salts": ("integrated-science", "sci-chemical-changes"),
    "Energy, Work & Power": ("integrated-science", "sci-energy"),
    "Light & Optics": ("integrated-science", "sci-energy"),
    "Magnetism": ("integrated-science", "sci-electricity"),
    "Electricity & Circuits": ("integrated-science", "sci-electricity"),
    "Forces & Motion": ("integrated-science", "sci-forces"),
    "Ecosystems, Food Chains & Ecology": ("integrated-science", "sci-environment"),
    "Earth, Rocks & Resources": ("integrated-science", "sci-environment"),
    "Meteorology, Weather & Environment": ("integrated-science", "sci-environment"),
    "Reproduction in Plants & Animals": ("integrated-science", "sci-living-things"),
    "Classification of Living Things": ("integrated-science", "sci-living-things"),
    "Cell Biology & Organisation": ("integrated-science", "sci-living-things"),
    "Photosynthesis & Plant Nutrition": ("integrated-science", "sci-living-things"),
    "Nutrition & Digestion": ("integrated-science", "sci-living-things"),
    "Human Body Systems": ("integrated-science", "sci-living-things"),
    "Respiration & Gas Exchange": ("integrated-science", "sci-living-things"),
    "Disease, Prevention & Health": ("integrated-science", "sci-health"),
    # Social Studies
    "Physical Geography & Map Reading": ("social-studies", "sst-physical-environment"),
    "Environmental Management & Climate": ("social-studies", "sst-physical-environment"),
    "Natural Resources & Their Management": ("social-studies", "sst-physical-environment"),
    "Population, Migration & Settlement": ("social-studies", "sst-human-environment"),
    "Economic Life: Industry, Trade & Commerce": ("social-studies", "sst-economics"),
    "Economic Life: Agriculture & Food": ("social-studies", "sst-economics"),
    "Colonial Period & Nationalism": ("social-studies", "sst-history-of-ghana"),
    "Pre-colonial Ghana History": ("social-studies", "sst-history-of-ghana"),
    "Independence, Republic & Political History": ("social-studies", "sst-history-of-ghana"),
    "Government, Democracy & Political Institutions": ("social-studies", "sst-government"),
    "Ghana Constitution & Rule of Law": ("social-studies", "sst-government"),
    "Global Organisations: UN, WHO, IMF": ("social-studies", "sst-government"),
    "Regional Integration: ECOWAS & AU": ("social-studies", "sst-government"),
    "Citizenship & Human Rights": ("social-studies", "sst-citizenship"),
    "Culture, Values, Traditions & Religion": ("social-studies", "sst-social-issues"),
    "Health, Hygiene & Social Issues": ("social-studies", "sst-social-issues"),
    "Family Life & Gender": ("social-studies", "sst-social-issues"),
    # RME
    "Moral Values: Honesty, Respect & Integrity": ("rme", "rme-moral-values"),
    "Social Responsibilities & Community Life": ("rme", "rme-moral-values"),
    "Family Life & Relationships": ("rme", "rme-moral-values"),
    "Christian Faith, Beliefs & Creeds": ("rme", "rme-christianity"),
    "Life & Teachings of Jesus Christ": ("rme", "rme-christianity"),
    "New Testament Church & Epistles": ("rme", "rme-christianity"),
    "Islamic Faith & Five Pillars": ("rme", "rme-islam"),
    "Quranic Teachings & Practice": ("rme", "rme-islam"),
    "Life of Prophet Muhammad": ("rme", "rme-islam"),
    "African Traditional Religion: Beliefs & Rituals": ("rme", "rme-traditional-religion"),
    "African Traditional Religion: Sacred Beings": ("rme", "rme-traditional-religion"),
    "Prayer, Worship & Festivals": ("rme", "rme-worship"),
    # Career technology and pre-technical skills
    "Wood & Metal Technology": ("bdt", "bdt-woodwork"),
    "Woodwork & Carpentry": ("bdt", "bdt-woodwork"),
    "Metalwork": ("bdt", "bdt-metalwork"),
    "Technical Drawing & Sketching": ("bdt", "bdt-technical-drawing"),
    "Electrical Work & Installations": ("bdt", "bdt-electronics"),
    "Electrical & Electronics Technology": ("bdt", "bdt-electronics"),
    "Workshop Tools & Safety": ("bdt", "bdt-tools-safety"),
    "Entrepreneurship & Business Skills": ("bdt", "bdt-enterprise"),
    "Material Properties & Selection": ("bdt", "bdt-materials"),
    "Building & Construction": ("bdt", "bdt-construction"),
    "Food & Nutrition Technology": ("home-economics", "home-food-and-nutrition"),
    "Clothing, Textiles & Fashion": ("home-economics", "home-clothing-and-textiles"),
    "Home Management & Consumer Education": ("home-economics", "home-management"),
    "Childcare & Development": ("home-economics", "home-child-care"),
    "Health, Safety & First Aid": ("home-economics", "home-hygiene"),
    # Home economics
    "Sewing, Needlework & Design": ("home-economics", "home-clothing-and-textiles"),
    "Meal Planning & Preparation": ("home-economics", "home-food-and-nutrition"),
    "Food, Nutrition & Balanced Diet": ("home-economics", "home-food-and-nutrition"),
    "Home Management & Budgeting": ("home-economics", "home-management"),
    "Family Life & Consumer Education": ("home-economics", "home-management"),
    "Food Safety, Hygiene & Preservation": ("home-economics", "home-hygiene"),
    "First Aid & Emergency Care": ("home-economics", "home-hygiene"),
    "Personal Health & Hygiene": ("home-economics", "home-hygiene"),
    "Clothing, Textiles & Laundry": ("home-economics", "home-clothing-and-textiles"),
    # French
    "French Vocabulary & Word Meaning": ("french", "fre-vocabulary"),
    "Everyday Conversation & Dialogue": ("french", "fre-greetings"),
    "French Grammar: Verbs & Tenses": ("french", "fre-verbs"),
    "French Grammar: Pronouns & Adjectives": ("french", "fre-grammar"),
    "French Grammar: Nouns & Articles": ("french", "fre-grammar"),
    # ICT and computing
    "Word Processing": ("ict", "ict-word-processing"),
    "Word Processing Applications": ("ict", "ict-word-processing"),
    "Computer Hardware & Components": ("ict", "ict-hardware"),
    "Computer Software & Operating Systems": ("ict", "ict-software"),
    "Data Storage & File Management": ("ict", "ict-hardware"),
    "Internet, Email & Web Browsing": ("ict", "ict-internet-safety"),
    "Computer Safety, Security & Ethics": ("ict", "ict-internet-safety"),
    "Spreadsheets": ("ict", "ict-spreadsheets"),
    "Spreadsheet Applications": ("ict", "ict-spreadsheets"),
    "Presentation Software": ("ict", "ict-presentations"),
    "Programming Concepts & Algorithms": ("ict", "ict-programming"),
    "ICT & Society": ("ict", "ict-basics"),
    "Computer Networks & Communication": ("ict", "ict-networks"),
    # Ghanaian languages and culture
    "Ga Grammar & Sentence Structure": ("ghanaian-language", "ghc-grammar"),
    "Asante Twi Grammar & Sentence Structure": ("ghanaian-language", "ghc-grammar"),
    "Writing in Ga": ("ghanaian-language", "ghc-grammar"),
    "Ga Phonology & Pronunciation": ("ghanaian-language", "ghc-grammar"),
    "Twi Phonology & Tone": ("ghanaian-language", "ghc-grammar"),
    "Ga Vocabulary & Word Meaning": ("ghanaian-language", "ghc-vocabulary"),
    "Asante Twi Vocabulary & Word Meaning": ("ghanaian-language", "ghc-vocabulary"),
    "Ga Culture, Traditions & Customs": ("ghanaian-language", "ghc-cultural-values"),
    "Akan Culture, Traditions & Customs": ("ghanaian-language", "ghc-cultural-values"),
    "Ga Oral Literature & Storytelling": ("ghanaian-language", "ghc-folktales"),
    "Akan Oral Literature & Storytelling": ("ghanaian-language", "ghc-folktales"),
    "Ga Proverbs, Idioms & Figurative Language": ("ghanaian-language", "ghc-proverbs"),
    "Twi Proverbs, Idioms & Figurative Language": ("ghanaian-language", "ghc-proverbs"),
}

# These need a passage or figure that is not part of the bank.
SKIP_TOPICS = re.compile(r"comprehension|cloze|literature appreciation|crop production|agricultural technology|^none$", re.I)
VISUAL = re.compile(
    r"\b(diagram|figure|chart|graph|table|mapping|magic square|shaded|pictogram|scale drawing|below|above)\b",
    re.I,
)
PREFIX = {
    "english": "neng", "integrated-science": "nsci", "social-studies": "nsst", "rme": "nrme",
    "bdt": "nbdt", "home-economics": "nhome", "french": "nfre", "ict": "nict",
    "ghanaian-language": "nghc",
}


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
        year = int(path.stem.rsplit("_", 1)[1])
        for obj in json.loads(path.read_text()):
            for q in obj["questions"]:
                source_topic = norm(q.get("topic") or "")
                mapping = TOPIC_MAP.get(source_topic)
                if not mapping or SKIP_TOPICS.search(source_topic):
                    skipped["topic not mapped / needs passage"] += 1
                    continue
                subject, topic = mapping
                prompt = norm(q.get("question"))
                explanation = norm(q.get("explanation"))
                answer = norm(q.get("answer")).upper()
                opts = q.get("options") or {}
                if answer not in "ABCD" or len(answer) != 1:
                    skipped["no answer"] += 1
                    continue
                if len(prompt) < 15 or len(prompt) > 600 or VISUAL.search(prompt):
                    skipped["bad prompt / needs figure"] += 1
                    continue
                if any(not norm(opts.get(k)) for k in "ABCD"):
                    skipped["missing option"] += 1
                    continue
                if any(re.search(r"\{\{|\}\}|\(\(|\)\)", norm(opts[k])) for k in "ABCD"):
                    skipped["malformed option"] += 1
                    continue
                # English "word closest in meaning/opposite" sections lose their
                # section heading in the source; without it the key is ambiguous.
                # The same happens when I/II/III statements are not in the prompt.
                clear_task = re.compile(r"\?|\.{3,}|\bmeans?\b|refers to|this means|which|what|choose|find|complete|state|name|give|define|explain", re.I)
                roman_combo = re.compile(r"^(?:(?:I|II|III|IV)(?: and (?:I|II|III|IV))? only)$")
                if subject == "english" and not clear_task.search(prompt) and all(len(norm(opts[k])) <= 35 for k in "ABCD"):
                    skipped["missing section instruction"] += 1
                    continue
                if all(roman_combo.match(norm(opts[k])) for k in "ABCD") and not re.search(r"\bI\.\s|\bII\.\s|\bIII\.\s|\bIV\.\s", prompt):
                    skipped["missing I/II/III statements"] += 1
                    continue
                key = dedupe_key(prompt)
                if key in seen:
                    skipped["duplicate"] += 1
                    continue
                seen.add(key)
                letter = "ABCD".index(answer)
                if len(explanation) < 40:
                    explanation = (f"Published BECE answer key, {year} Paper 1: {answer}. "
                                   f"{norm(opts[answer]).rstrip(' .')}. The source paper gives no worked solution.")
                prefix = PREFIX[subject]
                idx = 1
                while f"{prefix}-{year}-{idx:03d}" in ids:
                    idx += 1
                qid = f"{prefix}-{year}-{idx:03d}"
                ids.add(qid)
                added.append({
                    "id": qid,
                    "subject": subject,
                    "year": year,
                    "paper": 1,
                    "topic": topic,
                    "prompt": prompt,
                    "options": [norm(opts[k]) for k in "ABCD"],
                    "answerIndex": letter,
                    "explanation": explanation,
                })

    print(f"existing={len(bank)} added={len(added)} skipped={dict(skipped)}")
    print("by subject:", dict(Counter(q["subject"] for q in added)))
    print("by year:", dict(sorted(Counter(q["year"] for q in added).items())))
    print("topics used:", len(set(q["topic"] for q in added)))
    if args.dry_run:
        for q in added[:5]:
            print(json.dumps(q, ensure_ascii=False)[:400])
        return
    merged = bank + added
    args.bank.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {len(merged)} questions to {args.bank}")


if __name__ == "__main__":
    main()
