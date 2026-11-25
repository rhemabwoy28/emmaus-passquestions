# Emmaus Static Replica Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a pixel-close, BECE-only static replica of the GhLearner public UX under `/root/emmaus-passquestions/` with the Emmaus brand and the user's own archive data.

**Architecture:** One shared CSS token/component file and one vanilla JS interaction file. A small Python build script reads `assets/data/papers.json` and a shared HTML template to emit all pages, so paper/topic pages stay DRY. No backend, no external requests.

**Tech Stack:** HTML5, CSS custom properties, vanilla ES modules, Python 3 stdlib build script, git.

---

### Task 1: Scaffold project and generate paper data

**Objective:** Create the directory layout and a JSON inventory of BECE Maths papers from the local archive.

**Files:**
- Create: `/root/emmaus-passquestions/assets/data/papers.json`
- Create: `/root/emmaus-passquestions/tools/build_pages.py`
- Create: `/root/emmaus-passquestions/README.md`

**Step 1:** Inventory archive files with Python (`/root/jobsearch/bece_archive`, `bece2024`, `bece2025`); write years, paper numbers and local PDF names to `papers.json`.
**Step 2:** Create `tools/build_pages.py` skeleton that loads the JSON and prints the year count.
**Step 3:** Run `python3 tools/build_pages.py --inventory`, expected output: a count >= 20 year/paper entries.
**Step 4:** Commit: `git add . && git commit -m "feat: scaffold static replica and paper inventory"`.

### Task 2: Build shared CSS design system

**Objective:** Create fresh CSS reproducing the reference layout, tokens, components and responsive behaviour.

**Files:**
- Create: `/root/emmaus-passquestions/assets/site.css`

**Step 1:** Define tokens from measured reference values (`--rule`, `--paper`, `--ground`, `--chip`, ink, brand, whatsapp, telegram).
**Step 2:** Implement frame/section/button/pill/card/marquee/bubble/pixel-band/footer components.
**Step 3:** Add dark theme, focus states, reduced-motion and 390px/1280px breakpoints.
**Step 4:** Validate with `python3 -c "print(open('assets/site.css').read().count('{'))"` — expect > 40 rule blocks.
**Step 5:** Commit: `git commit -am "feat: add shared CSS design system"`.

### Task 3: Build shared JS interactions

**Objective:** Reimplement the reference interactions without a backend.

**Files:**
- Create: `/root/emmaus-passquestions/assets/site.js`

**Step 1:** Implement theme toggle with `localStorage` key `emmaus:theme` and pre-paint theme script inline in the template.
**Step 2:** Implement QOTD grading using `data-correct`, verdict `aria-live`, explanation reveal.
**Step 3:** Implement level tabs, mobile menu, marquee pause/play and local search filtering.
**Step 4:** Verify syntax with `node --check assets/site.js`, expected: no output, exit 0.
**Step 5:** Commit: `git commit -am "feat: add vanilla JS interactions"`.

### Task 4: Build HTML template and homepage

**Objective:** Create the shared template and a homepage matching the reference section order.

**Files:**
- Create: `/root/emmaus-passquestions/templates/base.html`
- Create: `/root/emmaus-passquestions/index.html`

**Step 1:** Build `base.html` with header, nav, search, footer, theme pre-paint script and `{{CONTENT}}` placeholder.
**Step 2:** Build homepage sections: hero with QOTD, how-it-works chat bubbles, activity marquee, stats, channels, study modes, apps, closing CTA.
**Step 3:** Replace all reference branding/copy/stats/bot links with Emmaus content; no external requests.
**Step 4:** Run generator to emit `index.html`; open in browser and check no console errors.
**Step 5:** Commit: `git commit -am "feat: add template and homepage"`.

### Task 5: Generate BECE subject, topic and paper pages

**Objective:** Emit all BECE pages from the template and paper inventory.

**Files:**
- Create: `/root/emmaus-passquestions/bece/index.html`
- Create: `/root/emmaus-passquestions/bece/mathematics.html`
- Create: `/root/emmaus-passquestions/bece/topics/index.html`
- Create: `/root/emmaus-passquestions/bece/topics/<slug>.html` (generated)
- Create: `/root/emmaus-passquestions/bece/papers/<year>/paper-<n>.html` (generated)

**Step 1:** Generate subject hub with paper counts and year list from `papers.json`.
**Step 2:** Generate topic pages for the maths topic list used in the reference UX (number, algebra, geometry, statistics, etc.).
**Step 3:** Generate one page per year/paper with links to the local archive PDFs where available.
**Step 4:** Run generator and assert file count >= 25.
**Step 5:** Commit: `git commit -am "feat: generate BECE pages"`.

### Task 6: Generate informational and utility pages

**Objective:** Emit about, contact, privacy, terms, download, leaderboard, sign-in and search pages.

**Files:**
- Create: `/root/emmaus-passquestions/about.html`, `contact.html`, `privacy.html`, `terms.html`, `download.html`, `leaderboard.html`, `sign-in.html`, `search.html`

**Step 1:** Write original copy for each page; mark contact details and leaderboard rows as demo placeholders.
**Step 2:** Sign-in page is visual only: form has `action="#"` and a visible notice that accounts are not enabled in the static build.
**Step 3:** Search page filters a local JS-backed list of papers/topics.
**Step 4:** Run generator, verify all 8 files exist.
**Step 5:** Commit: `git commit -am "feat: add informational pages"`.

### Task 7: Browser verification and fixes

**Objective:** Confirm visual fidelity, interactions and link integrity.

**Files:** Modify any file found broken.

**Step 1:** Serve locally with `python3 -m http.server 8765` from project root.
**Step 2:** Open in browser at 390px and 1280px; capture screenshots and compare section order/density with the reference.
**Step 3:** Exercise QOTD, tabs, theme, mobile menu, marquee, search; check console for errors.
**Step 4:** Run a link checker over local `href` values; expected: zero broken internal links.
**Step 5:** Fix anything found, then commit: `git commit -am "fix: verification issues"`.

### Task 8: Final report

**Objective:** Record what was built and what remains.

**Files:**
- Modify: `/root/emmaus-passquestions/README.md`

**Step 1:** Document run command, page inventory, data source and rights caveat.
**Step 2:** Commit: `git commit -am "docs: finalize README"`.

---

Plan complete. Execution approach: implement task-by-task with browser verification after each major group.
