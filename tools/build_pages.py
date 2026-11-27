#!/usr/bin/env python3
"""Build the Emmaus static replica from a shared template + local BECE inventory."""
from __future__ import annotations
import json, os, re, shutil, sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates/base.html").read_text()
DATA = ROOT / "assets/data/papers.json"
ARCHIVE = Path("/root/jobsearch/bece_archive")
EXTRA = [Path("/root/jobsearch/bece2024"), Path("/root/jobsearch/bece2025")]

YEARS = list(range(1990, 2027))
SUBJECTS = [
    {"slug": "mathematics", "name": "Mathematics", "topics": [
        ("number-bases", "Number bases"), ("fractions-decimals", "Fractions and decimals"),
        ("indices", "Indices and standard form"), ("algebra", "Algebra"),
        ("equations", "Equations and inequalities"), ("geometry", "Geometry"),
        ("mensuration", "Mensuration"), ("trigonometry", "Trigonometry"),
        ("statistics", "Statistics and probability"), ("sets", "Sets"),
    ]},
    {"slug": "english", "name": "English Language", "topics": [
        ("eng-comprehension", "Comprehension"), ("eng-vocabulary", "Vocabulary"),
        ("eng-grammar", "Grammar and structure"), ("eng-spelling", "Spelling and dictation"),
        ("eng-summary", "Summary writing"), ("eng-composition", "Composition"),
        ("eng-oral", "Oral English"),
    ]},
    {"slug": "integrated-science", "name": "Integrated Science", "topics": [
        ("sci-matter", "Matter"), ("sci-energy", "Energy"), ("sci-living-things", "Living things"),
        ("sci-environment", "Environment"), ("sci-health", "Health and safety"),
        ("sci-electricity", "Electricity"), ("sci-forces", "Forces and machines"),
        ("sci-chemical-changes", "Chemical changes"),
    ]},
    {"slug": "social-studies", "name": "Social Studies", "topics": [
        ("sst-citizenship", "Citizenship"), ("sst-physical-environment", "Physical environment"),
        ("sst-human-environment", "Human environment"), ("sst-history-of-ghana", "History of Ghana"),
        ("sst-government", "Government"), ("sst-economics", "Economics"),
        ("sst-social-issues", "Social issues"),
    ]},
    {"slug": "rme", "name": "Religious & Moral Education", "topics": [
        ("rme-christianity", "Christianity"), ("rme-islam", "Islam"),
        ("rme-traditional-religion", "Traditional religion"), ("rme-moral-values", "Moral values"),
        ("rme-worship", "Worship"), ("rme-festivals", "Religious festivals"),
    ]},
    {"slug": "bdt", "name": "Basic Design & Technology", "topics": [
        ("bdt-woodwork", "Woodwork"), ("bdt-metalwork", "Metalwork"),
        ("bdt-technical-drawing", "Technical drawing"), ("bdt-electronics", "Electronics"),
        ("bdt-design", "Design and graphics"), ("bdt-tools-safety", "Tools and safety"),
    ]},
    {"slug": "home-economics", "name": "Home Economics", "topics": [
        ("home-food-and-nutrition", "Food and nutrition"),
        ("home-clothing-and-textiles", "Clothing and textiles"),
        ("home-management", "Home management"), ("home-child-care", "Child care"),
        ("home-hygiene", "Hygiene and sanitation"), ("home-cooking", "Cooking and baking"),
    ]},
    {"slug": "ghanaian-language", "name": "Ghanaian Language & Culture", "topics": [
        ("ghc-proverbs", "Proverbs"), ("ghc-idioms", "Idioms"), ("ghc-folktales", "Folktales"),
        ("ghc-grammar", "Grammar"), ("ghc-comprehension", "Comprehension"),
        ("ghc-cultural-values", "Cultural values"), ("ghc-translation", "Translation"),
    ]},
    {"slug": "french", "name": "French", "topics": [
        ("fre-greetings", "Greetings"), ("fre-numbers", "Numbers"), ("fre-colours", "Colours"),
        ("fre-family", "Family"), ("fre-school", "School"), ("fre-verbs", "Verbs"),
        ("fre-questions", "Asking questions"),
    ]},
    {"slug": "ict", "name": "ICT & Computing", "topics": [
        ("ict-basics", "Computer basics"), ("ict-hardware", "Hardware"),
        ("ict-software", "Software"), ("ict-internet-safety", "Internet safety"),
        ("ict-word-processing", "Word processing"), ("ict-spreadsheets", "Spreadsheets"),
        ("ict-programming", "Programming basics"),
    ]},
]
TOPICS = [t for s in SUBJECTS for t in s["topics"]]

SAMPLE_QUESTIONS = [
    {
        "prompt": "If 3x + 7 = 22, what is the value of x?",
        "options": [("A", "5", True), ("B", "7", False), ("C", "9", False), ("D", "15", False)],
        "explanation": "Subtract 7 from both sides: 3x = 15. Divide by 3: x = 5. Check: 3(5) + 7 = 22.",
    }
]


def inventory() -> dict:
    """Years are indexed from the local archive; PDF links point at files we copy into the site."""
    safe_by_year = {
        2024: ["BECE2024_MATHEMATICS_ACTUAL_PAPER.pdf", "BECE2024_Mathematics_Paper2_Essay.pdf"],
        2025: ["BECE-2025-Mathematics-Paper1-OBJECTIVE-40-questions.pdf",
               "BECE-2025-Mathematics-Paper2-ESSAY-questions.pdf"],
    }
    years = []
    for y in YEARS:
        files = safe_by_year.get(y, [])
        papers = [
            {"no": 1, "label": "Paper 1 · Objective", "file": files[0] if files else None},
            {"no": 2, "label": "Paper 2 · Essay", "file": files[1] if len(files) > 1 else None},
        ]
        years.append({"year": y, "papers": papers})
    subjects = [
        {"slug": s["slug"], "name": s["name"],
         "topics": [{"slug": slug, "name": name, "subject": s["slug"]} for slug, name in s["topics"]]}
        for s in SUBJECTS
    ]
    return {
        "years": years,
        "subjects": subjects,
        "topics": [t for s in subjects for t in s["topics"]],
        "questions": SAMPLE_QUESTIONS,
    }


def load_data(force: bool = False) -> dict:
    if force or not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        data = inventory()
        DATA.write_text(json.dumps(data, indent=2))
        return data
    return json.loads(DATA.read_text())


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(rel: str, title: str, content: str, active: str = "") -> None:
    depth = rel.count("/")
    prefix = "../" * depth if depth else ""
    active_attr = lambda key: 'aria-current="page"' if active == key else ""
    html = (TEMPLATE
            .replace("{{ROOT}}", prefix)
            .replace("{{TITLE}}", esc(title))
            .replace("{{ACTIVE_BECE}}", active_attr("bece"))
            .replace("{{ACTIVE_TOPICS}}", active_attr("topics"))
            .replace("{{ACTIVE_LEADERBOARD}}", active_attr("leaderboard"))
            .replace("{{ACTIVE_ABOUT}}", active_attr("about"))
            .replace("{{CONTENT}}", content))
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def qotd(data: dict) -> str:
    q = data["questions"][0]
    opts = "".join(
        f'<button class="option" type="button" data-correct="{str(c).lower()}">'
        f'<span class="letter">{letter}</span><span>{esc(text)}</span></button>'
        for letter, text, c in q["options"]
    )
    return f'''
<section class="section" id="question-of-the-day">
  <div class="wrap">
    <div class="q-card" data-quiz data-qotd>
      <div class="q-head"><span class="pill"><span class="pill-dot"></span> Question of the day</span><span class="muted small">BECE Mathematics · offline demo</span></div>
      <div class="q-text">{esc(q['prompt'])}</div>
      <div class="options">{opts}</div>
      <div class="verdict hidden" data-verdict></div>
      <div class="explanation hidden" data-explanation><strong>Working:</strong> {esc(q['explanation'])}</div>
      <div class="gate hidden" data-gate>
        <p class="small">That is the idea: answer a real-style question, see the marking, then go deeper.</p>
        <a class="btn btn-primary btn-sm" href="practice.html">Practise the full paper</a>
      </div>
    </div>
  </div>
</section>'''


def home(data: dict, questions: list) -> str:
    years = data["years"]
    practice_count = len(questions)
    activity = "".join(
        f'<div class="marquee-item"><strong>{y["year"]}</strong> Mathematics paper added · BECE</div>'
        for y in years[-12:]
    ) * 2
    return f'''
<section class="hero">
  <div class="wrap">
    <span class="pill"><span class="pill-dot"></span> BECE revision, free on any phone</span>
    <h1 style="margin-top:16px">Pass your BECE.<br><span>Free.</span></h1>
    <p class="lead">Practise BECE questions across every subject and topic, check the working, and walk into the exam hall knowing what to expect.</p>
    <div class="hero-actions">
      <a class="btn btn-wa" href="bece/index.html">Browse all subjects</a>
      <a class="btn btn-outline" href="practice.html">Start practising</a>
    </div>
    <p class="hero-foot">No payment. No app required. Works on any phone.</p>
    <p style="margin-top:18px"><a class="pill" href="#question-of-the-day"><span class="pill-dot"></span> Question of the day · try one now ↓</a></p>
  </div>
</section>

<section class="section" aria-label="How it works">
  <div class="wrap">
    <div class="eyebrow">How it works</div>
    <h2>From your first question to a full paper</h2>
    <div class="bubbles" style="margin-top:20px">
      <div class="window">
        <div class="window-bar"><span class="dot"></span> Emmaus · chat</div>
        <div class="window-body">
          <div class="bubble in">Hi, I want to revise for BECE Maths</div>
          <div class="bubble out">Welcome 👋 Pick a year to see the papers we have.</div>
          <div class="bubble in">2025</div>
          <div class="bubble out">Paper 1 and Paper 2 are ready. Open the paper to start.</div>
        </div>
      </div>
      <div class="window">
        <div class="window-bar"><span class="dot" style="background:var(--brand)"></span> Web · question view</div>
        <div class="window-body">
          <div class="bubble in">Which topic needs work?</div>
          <div class="bubble out">Statistics and probability · 12 questions</div>
          <div class="bubble in">Show the marking scheme</div>
          <div class="bubble out">Step-by-step working is under every answer.</div>
        </div>
      </div>
      <div class="window">
        <div class="window-bar"><span class="dot" style="background:var(--accent)"></span> Offline · saved paper</div>
        <div class="window-body">
          <div class="bubble in">Saved for the trotro ride home</div>
          <div class="bubble out">2024 Mathematics Paper 1 · 40 questions · available offline</div>
          <div class="bubble in">I finished. What next?</div>
          <div class="bubble out">Your score is ready. Try a mock under timed conditions.</div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section-tight" aria-label="Recently added">
  <div class="marquee-band" data-marquee>
    <div class="marquee-viewport"><div class="marquee-track">{activity}</div></div>
    <button class="marquee-toggle" type="button" data-marquee-toggle aria-pressed="false">Pause</button>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid grid-4">
      <div class="stat"><b>{len(data["subjects"])}</b><span class="small">BECE subjects</span></div>
      <div class="stat"><b>{len(data["topics"])}</b><span class="small">topics covered</span></div>
      <div class="stat"><b>{practice_count}</b><span class="small">practice questions</span></div>
      <div class="stat"><b>0</b><span class="small">payment, ever</span></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow">Start with one question</div>
    <h2>Answer a real-style question, then go deeper</h2>
    <p class="lead" style="margin:10px 0 18px">A new practice question every day. No account and no payment to see the working.</p>
    {qotd(data)}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2>Study however you get online</h2>
    <div class="grid grid-3" style="margin-top:18px">
      <div class="card"><h3>On your phone</h3><p>Download the papers once, then revise with no data at all — on the trotro, at home, anywhere.</p><div class="card-actions"><a class="btn btn-quiet btn-sm" href="download.html">Get the PDFs</a></div></div>
      <div class="card"><h3>On the web</h3><p>Open a year, pick a paper, and work through every question with the marking scheme beside you.</p><div class="card-actions"><a class="btn btn-quiet btn-sm" href="bece/index.html">Browse BECE</a></div></div>
      <div class="card"><h3>By topic</h3><p>Weak in mensuration? Practise that topic across years instead of starting from page one.</p><div class="card-actions"><a class="btn btn-quiet btn-sm" href="bece/topics/index.html">See topics</a></div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap center">
    <h2>Start revising today</h2>
    <p class="lead" style="margin:10px auto 18px;max-width:620px">Every question you answer shows you something new about what you know. Pick a year and begin.</p>
    <a class="btn btn-primary" href="bece/index.html">Explore BECE past papers</a>
  </div>
</section>'''


def bece_hub(data: dict, questions: list) -> str:
    rows = "".join(
        f'<li><a href="papers/{y["year"]}/paper-{p["no"]}.html">{y["year"]} · {esc(p["label"])}</a><span class="muted small">Mathematics</span></li>'
        for y in data["years"] for p in y["papers"]
    )
    subjects = "".join(
        f'<div class="card"><h3><a href="{s["slug"]}.html">{esc(s["name"])}</a></h3>'
        f'<p class="small">{len(s["topics"])} topics · {sum(1 for q in questions if q.get("subject") == s["slug"])} practice questions</p></div>'
        for s in data["subjects"]
    )
    return f'''
<section class="section"><div class="wrap">
  <span class="pill">BECE · Junior High</span>
  <h1 style="margin-top:14px">BECE past questions</h1>
  <p class="lead" style="margin:10px 0 22px">Practice questions and topics for every BECE subject, plus the Mathematics paper archive by year.</p>
  <h2>Subjects</h2><div class="grid grid-3" style="margin:16px 0 28px">{subjects}</div>
  <div class="card"><h3>Browse topics</h3><p class="small">Algebra, comprehension, integrated science, social studies and more — across all subjects.</p><div class="card-actions"><a class="btn btn-quiet btn-sm" href="topics/index.html">See all topics</a></div></div>
  <h2 style="margin-top:28px">Past papers by year</h2>
  <div class="table-wrap"><ul class="list">{rows}</ul></div>
</div></section>'''


def subject_page(subject: dict, data: dict, questions: list) -> str:
    subject_questions = [q for q in questions if q.get("subject") == subject["slug"]]
    topic_rows = "".join(
        f'<li><a href="topics/{t["slug"]}.html">{esc(t["name"])}</a>'
        f'<span class="muted small">{sum(1 for q in subject_questions if q["topic"] == t["slug"])} questions</span></li>'
        for t in subject["topics"]
    )
    rows = ""
    if subject["slug"] == "mathematics":
        rows = "".join(
            f'<li><a href="papers/{y["year"]}/paper-{p["no"]}.html">{y["year"]} · {esc(p["label"])}</a><span class="muted small">{"PDF available" if p["file"] else "index only"}</span></li>'
            for y in data["years"] for p in y["papers"]
        )
    return f'''
<section class="section"><div class="wrap">
  <p class="small"><a href="index.html">BECE</a> / {esc(subject['name'])}</p>
  <h1 style="margin:10px 0">BECE {esc(subject['name'])}</h1>
  <p class="lead">Original BECE-style practice questions and topics for {esc(subject['name'])}, with working for every answer.</p>
  <div class="grid grid-3" style="margin:20px 0">
    <div class="stat"><b>{len(subject['topics'])}</b><span class="small">topics</span></div>
    <div class="stat"><b>{len(subject_questions)}</b><span class="small">practice questions</span></div>
    <div class="stat"><b>0</b><span class="small">payment, ever</span></div>
  </div>
  <div class="card-actions" style="margin-bottom:24px"><a class="btn btn-primary btn-sm" href="../practice.html?subject={subject['slug']}">Practise {esc(subject['name'])}</a><a class="btn btn-quiet btn-sm" href="topics/index.html">All topics</a></div>
  <h2>Topics</h2><ul class="list">{topic_rows}</ul>
  {'<h2 style="margin-top:28px">Archived papers</h2><ul class="list">' + rows + '</ul>' if rows else ''}
</div></section>'''


def topics_index(data: dict, questions: list) -> str:
    blocks = []
    for s in data["subjects"]:
        cards = "".join(
            f'<div class="card"><h3><a href="{t["slug"]}.html">{esc(t["name"])}</a></h3>'
            f'<p class="small">{sum(1 for q in questions if q["topic"] == t["slug"])} practice questions</p></div>'
            for t in s["topics"]
        )
        blocks.append(
            f'<h2 style="margin-top:26px"><a href="../{s["slug"]}.html">{esc(s["name"])}</a></h2>'
            f'<div class="grid grid-3" style="margin-top:12px">{cards}</div>'
        )
    return ('<section class="section"><div class="wrap"><h1>BECE topics by subject</h1>'
            '<p class="lead" style="margin:10px 0 20px">Pick a subject, then a topic, and work through questions with the marking scheme.</p>'
            + "".join(blocks) + '</div></section>')


def topic_page(t: dict, data: dict, questions: list) -> str:
    subject = next(s for s in data["subjects"] if s["slug"] == t["subject"])
    topic_questions = [q for q in questions if q["topic"] == t["slug"]]
    samples = "".join(
        f'<li><span>{esc(q["prompt"])}</span><span class="muted small">'
        f'<a href="../../practice.html?subject={t["subject"]}&amp;topic={t["slug"]}&amp;year={q["year"]}">Answer →</a></span></li>'
        for q in topic_questions[:6]
    )
    related = ""
    if t["subject"] == "mathematics":
        rows = "".join(
            f'<li><a href="../papers/{y["year"]}/paper-1.html">{y["year"]} Paper 1</a><span class="muted small">PDF</span></li>'
            for y in data["years"][-10:]
        )
        related = f'<h2 style="margin-top:24px">Related papers</h2><ul class="list">{rows}</ul>'
    return f'''<section class="section"><div class="wrap">
  <p class="small"><a href="index.html">Topics</a> / <a href="../{t['subject']}.html">{esc(subject['name'])}</a> / {esc(t['name'])}</p>
  <h1 style="margin:10px 0">{esc(t['name'])}</h1>
  <p class="lead">Practise {esc(t['name']).lower()} with BECE-style {esc(subject['name'])} questions and see the working for every answer.</p>
  <div class="card" style="margin:18px 0">
    <h3>{len(topic_questions)} practice question{'s' if len(topic_questions) != 1 else ''} available</h3>
    <p class="small">Timed by you, marked on this device, no account needed.</p>
    <div class="card-actions"><a class="btn btn-primary btn-sm" href="../../practice.html?subject={t['subject']}&amp;topic={t['slug']}">Practise {esc(t['name']).lower()}</a></div>
  </div>
  {'<h2>Sample questions</h2><ul class="list">' + samples + '</ul>' if samples else ''}
  {related}
</div></section>'''


def paper_page(year: int, paper: dict, prefix: str) -> str:
    file = paper.get("file")
    if os.environ.get("EMMAUS_PUBLIC"):
        note = "The PDF is kept in the local archive and is not published online."
        actions = f'<span class="muted small">PDF available locally — not published online.</span>'
        rights = "This hosted version publishes only the practice pages; archived PDFs stay local."
    else:
        link = f'{prefix}papers/BECE_Mathematics_1990-2026_MERGED.pdf' if not file else f'{prefix}papers/{quote(file)}'
        note = "Opens the archived merged PDF (all years) in a new tab." if not file else "Opens the archived PDF in a new tab."
        actions = f'<a class="btn btn-primary btn-sm" href="{link}" target="_blank" rel="noopener">Open PDF</a>'
        rights = "Rights note: archived BECE papers are third-party reproductions. Keep this build local until publishing rights are confirmed."
    return f'''<section class="section"><div class="wrap">
  <p class="small"><a href="{prefix}bece/mathematics.html">BECE Mathematics</a> / {year}</p>
  <h1 style="margin:10px 0">{year} · {esc(paper['label'])}</h1>
  <p class="lead">Revision paper for BECE Mathematics. Work through the questions, then check the marking scheme.</p>
  <div class="card" style="margin-top:18px">
    <h3>Open the paper</h3>
    <p class="small">{note}</p>
    <div class="card-actions">{actions}<a class="btn btn-quiet btn-sm" href="{prefix}practice.html?subject=mathematics&amp;year={year}&amp;paper={paper['no']}">Practice this paper</a><a class="btn btn-quiet btn-sm" href="{prefix}bece/mathematics.html">All years</a></div>
  </div>
  <div class="notice" style="margin-top:18px">{rights}</div>
</div></section>'''


def practice_page(data: dict) -> str:
    years = "".join(f'<option value="{y["year"]}">{y["year"]}</option>' for y in data["years"])
    subjects = "".join(f'<option value="{s["slug"]}">{esc(s["name"])}</option>' for s in data["subjects"])
    topics = "".join(
        f'<option value="{t["slug"]}" data-subject="{t["subject"]}">{esc(t["name"])}</option>'
        for t in data["topics"]
    )
    return f'''<section class="section"><div class="wrap">
  <h1>Practice questions</h1>
  <p class="lead" style="margin:10px 0 18px">Answer BECE-style questions from every subject, see the working immediately, and keep your best score on this device. No account and no network calls.</p>
  <div class="notice" style="margin-bottom:18px">A mix of original practice questions and BECE English and Social Studies questions compiled from publicly available past papers. This is independent study material, not an official WAEC publication. The archived Mathematics PDFs remain available on each paper page.</div>
  <form class="card quiz-controls" data-practice-controls>
    <div class="grid grid-5">
      <div class="field"><label for="practice-subject">Subject</label><select id="practice-subject" data-practice-subject><option value="">All subjects</option>{subjects}</select></div>
      <div class="field"><label for="practice-year">Year</label><select id="practice-year" data-practice-year><option value="">All years</option>{years}</select></div>
      <div class="field"><label for="practice-paper">Paper</label><select id="practice-paper" data-practice-paper><option value="">All papers</option><option value="1">Paper 1 · Objective</option><option value="2">Paper 2 · Essay</option></select></div>
      <div class="field"><label for="practice-topic">Topic</label><select id="practice-topic" data-practice-topic><option value="">All topics</option>{topics}</select></div>
      <div class="field"><label for="practice-count">Questions</label><select id="practice-count" data-practice-count><option value="5">5</option><option value="10" selected>10</option><option value="0">All</option></select></div>
    </div>
    <button class="btn btn-primary btn-sm" type="submit">Start practice</button>
  </form>
  <div data-quiz-runner style="margin-top:20px"><p class="muted">Choose a filter and start practice.</p></div>
</div></section>'''


def simple(title: str, body: str) -> str:
    return f'<section class="section"><div class="wrap"><h1 style="margin-bottom:14px">{title}</h1><div class="stack">{body}</div></div></section>'


def build() -> None:
    data = load_data()
    questions = json.loads((ROOT / "assets/data/questions.json").read_text())
    (ROOT / "assets/questions.js").write_text(
        "(function (root, factory) { const data = factory(); "
        "if (typeof module !== 'undefined' && module.exports) module.exports = data; "
        "else root.QUESTION_BANK = data; })"
        "(typeof globalThis !== 'undefined' ? globalThis : this, function () { return "
        + json.dumps(questions, ensure_ascii=False) + "; });\n"
    )
    render("index.html", "Home", home(data, questions))
    render("bece/index.html", "BECE", bece_hub(data, questions), "bece")
    for s in data["subjects"]:
        render(f'bece/{s["slug"]}.html', f'BECE {s["name"]}', subject_page(s, data, questions), "bece")
    render("bece/topics/index.html", "Topics", topics_index(data, questions), "topics")
    for t in data["topics"]:
        render(f'bece/topics/{t["slug"]}.html', t["name"], topic_page(t, data, questions), "topics")
    for y in data["years"]:
        for p in y["papers"]:
            prefix = "../../../"
            render(f'bece/papers/{y["year"]}/paper-{p["no"]}.html',
                   f'{y["year"]} {p["label"]}', paper_page(y["year"], p, prefix), "bece")

    render("about.html", "About", simple("About Emmaus", '''
<p class="lead">Emmaus Methodist Pass Questions exists so that a student's preparation depends on effort, not on whether their school has the past papers or their family can afford a bookshop copy.</p>
<p>We organise BECE Mathematics papers by year and topic, keep the marking schemes next to the questions, and make everything work on a phone with a little data. There is no payment and no signup needed to browse.</p>
<div class="card"><h3>Honest limits</h3><p>We are not affiliated with WAEC or GES. Our papers are study copies, not official publications, and we cannot promise a grade.</p></div>'''), "about")
    render("contact.html", "Contact", simple("Contact", '''
<p class="lead">Spotted a mistake in a paper, or want to suggest a topic? Tell us and we will fix it.</p>
<div class="card"><h3>Demo contact details</h3><p class="small">Replace these placeholder details before publishing.</p><p>Email: <span class="mono">hello@example.org</span></p><p>Phone: <span class="mono">+233 00 000 0000</span></p></div>'''))
    render("privacy.html", "Privacy", simple("Privacy policy", '''
<p class="lead">This static demo collects nothing. There are no accounts, no analytics, no cookies and no network calls beyond loading these pages.</p>
<p>All question papers are stored locally in the site folder. If you publish a version with accounts, you must add a real privacy policy covering name, phone, progress and device data before collecting any of it.</p>'''))
    render("terms.html", "Terms", simple("Terms of service", '''
<p class="lead">Use the material here for your own study. Do not resell it, bulk-download it or republish it as your own.</p>
<p>BECE questions originate with WAEC. These files are third-party study reproductions kept in a local archive. Publishing or redistributing them may require permission — check rights before making this site public.</p>
<p>Automated marking, if added later, is a study aid and not an official assessment.</p>'''))
    download_action = ('<span class="muted small">The archive stays local and is not published online.</span>'
                       if os.environ.get("EMMAUS_PUBLIC") else
                       '<a class="btn btn-primary btn-sm" href="papers/BECE_Mathematics_1990-2026_MERGED.pdf">Open merged PDF</a>')
    render("download.html", "Download", simple("Download the papers", f'''
<p class="lead">The PDF archive lives in this project folder, so it can be opened offline once the site files are on your device.</p>
<div class="card"><h3>BECE Mathematics archive</h3><p class="small">1990–2026, merged into one PDF, plus verified 2024 and 2025 papers.</p><div class="card-actions">{download_action}</div></div>
<div class="notice" style="margin-top:18px">No app, no install, no data needed after download.</div>'''))
    render("leaderboard.html", "Leaderboard", simple("Leaderboard", '''
<p class="lead">A bit of friendly competition helps some students keep going. These demo rows are placeholders — your own best scores below are saved only on this device.</p>
<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Student</th><th>Points</th></tr></thead><tbody>
<tr><td>1</td><td>Demo Learner A</td><td>815</td></tr><tr><td>2</td><td>Demo Learner B</td><td>380</td></tr><tr><td>3</td><td>Demo Learner C</td><td>343</td></tr>
</tbody></table></div>
<div style="margin-top:24px" data-local-bests><h2>Your best scores</h2><p class="muted">Loading scores saved on this device…</p></div>'''), "leaderboard")
    render("sign-in.html", "Sign in", simple("Sign in", '''
<p class="lead">Accounts are not enabled in this static build. This page is here to match the reference layout.</p>
<form class="card auth-card" data-demo-form>
  <div class="field"><label for="phone">Phone number</label><input id="phone" name="phone" type="tel" placeholder="0XX XXX XXXX"></div>
  <button class="btn btn-primary" type="submit">Continue</button>
  <p class="small muted" style="margin-top:12px">Submitting shows a demo notice; nothing is sent anywhere.</p>
</form>'''))
    render("practice.html", "Practice", practice_page(data))
    links = "".join(
        f'<a class="hidden" data-searchable href="bece/papers/{y["year"]}/paper-{p["no"]}.html" data-kind="paper">{y["year"]} Mathematics {esc(p["label"])}</a>'
        for y in data["years"] for p in y["papers"]
    ) + "".join(
        f'<a class="hidden" data-searchable href="bece/{s["slug"]}.html" data-kind="subject">{esc(s["name"])}</a>'
        for s in data["subjects"]
    ) + "".join(
        f'<a class="hidden" data-searchable href="bece/topics/{t["slug"]}.html" data-kind="topic">{esc(t["name"])} · {esc(t["subject"].replace("-", " "))}</a>'
        for t in data["topics"]
    ) + "".join(
        (lambda haystack: (
          f'<a class="hidden" data-searchable="{esc(haystack)}" href="practice.html?subject={q["subject"]}&amp;year={q["year"]}&amp;topic={q["topic"]}" '
          f'data-kind="practice question">'
          f'{esc(q["subject"].replace("-", " "))} · {q["year"]} · {esc(q["topic"].replace("-", " "))} · {esc(q["prompt"])}</a>'
        ))(" ".join([q["subject"].replace("-", " "), q["topic"].replace("-", " "), q["prompt"], *q["options"]]))
        for q in questions
    )
    render("search.html", "Search", f'''<section class="section"><div class="wrap">
<h1>Search</h1><p class="lead" style="margin:10px 0">Search papers, topics and practice questions — all offline.</p>
<form class="card" data-search-form><div class="field"><label for="q">Search past questions, topics and years</label><input id="q" data-search-input type="search" placeholder="e.g. 2025 or statistics"></div><button class="btn btn-primary btn-sm" type="submit">Search</button></form>
{links}<div data-search-results style="margin-top:20px"><p class="muted">Type a year, topic or paper to search.</p></div>
</div></section>''')
    render("404.html", "Page not found", simple("Page not found", '''
<p class="lead">That page is not in this offline copy. The past papers and practice questions are still here.</p>
<div class="card-actions"><a class="btn btn-primary btn-sm" href="index.html">Go home</a><a class="btn btn-quiet btn-sm" href="bece/index.html">Browse BECE papers</a><a class="btn btn-quiet btn-sm" href="search.html">Search</a></div>'''))

    # Local PDFs: one merged archive plus verified 2024/2025 papers.
    pdfdir = ROOT / "papers"
    pdfdir.mkdir(exist_ok=True)
    merged = ARCHIVE / "BECE_Mathematics_1990-2026_MERGED.pdf"
    if merged.exists() and not (pdfdir / merged.name).exists():
        shutil.copy2(merged, pdfdir / merged.name)
    for base in EXTRA:
        for p in base.glob("*.pdf"):
            dest = pdfdir / p.name
            if not dest.exists():
                shutil.copy2(p, dest)

    pages = list(ROOT.rglob("*.html"))
    print(f"papers.json: {len(data['years'])} years, {len(data['topics'])} topics")
    print(f"generated {len(pages)} HTML pages")


if __name__ == "__main__":
    if "--inventory" in sys.argv:
        d = inventory()
        print(f"inventory: {len(d['years'])} years, {len(d['topics'])} topics")
    else:
        build()
