# Emmaus Methodist Pass Questions — static replica

A pixel-close, BECE-only reconstruction of the GhLearner public-page UX with original branding, copy and assets. No backend, no accounts, no analytics, no external requests.

## Live site

Public GitHub Pages build: https://rhemabwoy28.github.io/emmaus-passquestions/

The `main` branch is the local/source build (with PDF links). The `gh-pages` branch is generated with `EMMAUS_PUBLIC=1`, which replaces PDF links with a “PDF available locally” notice. To refresh it:

```bash
git checkout gh-pages
EMMAUS_PUBLIC=1 python3 tools/build_pages.py
git add -A && git commit -m 'Refresh Pages build'
git push origin gh-pages
```

## Run locally

```bash
cd /root/emmaus-passquestions
python3 -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/
```

## Rebuild pages after editing the template, CSS, JS or data

```bash
python3 tools/build_pages.py --inventory   # regenerate assets/data/papers.json
python3 tools/build_pages.py               # emit all HTML pages
```

## What is here

- 99 generated HTML pages: home, about, contact, privacy, terms, download, leaderboard, sign-in (visual only), search, practice, 404, BECE hub, Mathematics subject page, 10 topic pages, and 74 year/paper pages.
- Shared `assets/site.css` and `assets/site.js`, plus `assets/quiz-core.js` (pure scoring logic) and generated `assets/questions.js`.
- `assets/data/questions.json` holds 24 original BECE-style practice questions with explanations; `assets/data/papers.json` is the page index.
- Question of the day rotates automatically from the question bank, keyed to the UTC date.
- Topic pages link straight into filtered practice; practice can also filter by year, paper and topic.
- Search covers papers, topics and practice questions, and honours `?q=` links from the header search box.
- The leaderboard shows best scores saved on this device alongside the demo rows.
- `papers/` holds the local archive: the 1990–2026 merged BECE Mathematics PDF plus verified 2024/2025 Paper 1 and Paper 2 files.
- Design spec: `docs/superpowers/specs/2026-11-25-emmaus-static-replica-design.md`
- Implementation plan: `docs/plans/2026-11-25-emmaus-static-replica.md`

## Interactions verified in a browser

- Question-of-the-day grading, explanation reveal and signup gate.
- Desktop/mobile navigation and theme toggle.
- Activity marquee pause/play.
- Local search across papers and topics.
- Sign-in demo form notice (no data sent).
- 390px and 1280px layouts with no horizontal overflow.
- Zero broken internal links.
- Quiz engine: 10-question run scored 100%, explanations shown, best score saved locally, URL filters auto-start.
- Daily question rotation, topic-page practice links, year/paper/topic filters, `?q=` search results, local bests on the leaderboard and the 404 page — all checked at 390px and 1280px with no horizontal overflow.

## Tests and CI

```bash
python3 tools/build_pages.py   # generate assets/questions.js first
node --test tests/*.test.js    # expects 17 passing tests
python3 tools/check_links.py   # verifies local href/src targets
```

`.github/workflows/ci.yml` rebuilds the pages, asserts the generated files are committed, runs the Node tests and checks local links on every push and pull request to `main`.

The BECE PDFs are intentionally **not committed**. They stay in the local `papers/` folder (gitignored) because they are third-party study reproductions and the repo is private. After cloning on another machine, copy the archive into `papers/` manually; the generated paper pages link to those files.

## Rights caveat

The BECE PDFs in `papers/` are third-party study reproductions from a local archive, not official WAEC publications. This build is local-only. Confirm redistribution rights before publishing or deploying it publicly.

## Not included

Accounts/OTP, answer autosave, scoring, leaderboard writes, WhatsApp/Telegram bots and WASSCE content are deliberately out of scope for this static phase.
