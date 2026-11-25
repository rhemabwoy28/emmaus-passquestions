# Design: Emmaus Methodist Pass Questions — static replica

Date: 2026-11-25
Status: approved-by-user (design conversation), pending spec review

## Goal

Build a pixel-close, public-page-only replica of the GhLearner UX with the user's own brand (**Emmaus Methodist Pass Questions**) and the user's own BECE Mathematics archive. No backend, no network calls, no copying of GhLearner copy, branding, analytics IDs or question text from their site.

## Non-goals

- No accounts, OTP, database, scoring, bots, leaderboard data writes or deployed server.
- No WASSCE content (BECE only, per user decision).
- No republishing of GhLearner's assets, mark-up or CSS verbatim.
- No claim that the user's BECE PDFs are official WAEC publications (archive findings show they are third-party reproductions).

## Scope: pages

`index.html`, `about.html`, `contact.html`, `privacy.html`, `terms.html`, `download.html`, `leaderboard.html`, `sign-in.html`, `bece/index.html`, `bece/mathematics.html`, `bece/topics.html`, `bece/topics/<slug>.html`, `bece/papers/<year>/paper-<n>.html`, `search.html`.

Shared `assets/site.css`, `assets/site.js`, `assets/data/papers.json`, `assets/data/questions.json`.

## Visual system

Derived from computed styles of the reference site, reimplemented in fresh CSS:
- Tokens: `--rule:#dde1e8`, `--paper:#fff`, `--ground:#f7f8fa`, `--chip:#edeff3`, ink `#10151c`, brand blue/green accents, WhatsApp green and Telegram sky as channel accents.
- Type: Inter-like sans for UI, Outfit-like display for headings, monospace for numbers/labels.
- Layout: centred max-width frames, section borders, 4px spacing scale, responsive grids.
- Components: pill links, buttons (primary/quiet/whatsapp/telegram), marquee activity band, chat-bubble demo windows, pixel-band decorative strip, cards, footer.
- Interactions: level tabs, client-side QOTD grading with `data-correct`, explanation reveal, marquee pause/play, dark mode via `localStorage`, mobile menu, local search filter.
- Accessibility: semantic landmarks, 44px hit targets, focus rings, `aria-live` on verdict, reduced-motion handling.

## Content

- Brand name and promise replace all GhLearner strings.
- Paper/year listings generated from `/root/jobsearch/bece_archive` and `/root/jobsearch/bece2024|2025` inventories.
- Sample questions use original/paraphrased practice questions authored for this build, not text lifted from the reference site.
- Contact details are placeholders the user must replace (no phone/email copied from the reference site).
- Leaderboard uses obviously fictional sample rows labelled "demo data".

## Output location

`/root/emmaus-passquestions/` (local static site). Deployment to VPS nginx is a separate later task.

## Verification

- Browser open at 390px and 1280px; compare layout and density with the reference screenshots.
- No console errors, no broken internal links, no external requests from the page.
- Interactions exercised: QOTD answer, tabs, marquee toggle, theme toggle, mobile menu, search.
- File inventory checked against the page list above.

## Risks / notes

- BECE papers in the archive are third-party reproductions; publishing them may require rights clearance. Build stays local until the user confirms.
- Exact pixel match is not promised: fonts and SVG decorations are recreated, not copied.
