# Emmaus Visual Polish Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Refresh `assets/site.css` with the refined institutional-blue direction without touching HTML, JS or content.

**Architecture:** Single-file CSS token and component refinement. Static generator keeps producing identical HTML; only the shared stylesheet changes. Visual verification uses the live Pages build and local preview at 390/768/1280px.

**Tech Stack:** CSS custom properties, static HTML generator, Node test runner, browser harness.

---

### Task 1: Capture visual baseline

**Objective:** Record current screenshots and overflow state before editing.

- Run local preview on `http://127.0.0.1:8765` (already running).
- Capture home, practice, paper and maths pages at 390px, 768px and 1280px.
- Record `document.documentElement.scrollWidth <= innerWidth` for each.

**Verification:** baseline screenshots saved under `/root/.hermes/cache/scratch/polish-baseline/`.

### Task 2: Retune design tokens

**Objective:** Update the `:root` block in `assets/site.css` with the refined palette, radius/shadow/type/motion scales.

**Files:** Modify `assets/site.css` (top `:root`, lines 3-29).

**Step 1:** Replace the token block with:

```css
:root {
  --rule: #e3e7ee;
  --rule-strong: #c8d0dc;
  --paper: #ffffff;
  --ground: #f6f8fb;
  --chip: #eef2f7;
  --ink: #0f1722;
  --ink-600: #46536a;
  --ink-400: #79879b;
  --brand: #1a5c8c;
  --brand-dark: #14496f;
  --brand-deep: #0b3252;
  --brand-tint: #e8f1f8;
  --accent: #c2410c;
  --accent-soft: #fff0e4;
  --whatsapp: #25d366;
  --whatsapp-dark: #128c7e;
  --telegram: #2aabee;
  --telegram-dark: #17699a;
  --ok: #15803d;
  --bad: #b91c1c;
  --radius-sm: 10px;
  --radius: 14px;
  --radius-lg: 20px;
  --shadow: 0 8px 26px rgba(15, 23, 34, .07);
  --shadow-raised: 0 14px 38px rgba(15, 23, 34, .12);
  --ease: cubic-bezier(.2, .7, .3, 1);
  --dur: .18s;
  --maxw: 1100px;
  --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-display: Outfit, "Trebuchet MS", var(--font-sans);
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lead: 18px;
}
```

**Step 2:** Keep the existing `.dark` overrides, adding `--brand-tint: #15293b`.

**Step 3:** Verify no page references removed tokens. Run a CSS grep for `var(--shadow-raised)` usage after later tasks.

### Task 3: Normalise global elements and buttons

**Objective:** Replace hard-coded radii/transitions with tokens and explicit interaction states.

**Files:** Modify `assets/site.css` sections `Buttons and pills` (lines 90-105) and global rules (lines 40-54).

- `.btn` transition becomes `transform var(--dur) var(--ease), background var(--dur) var(--ease), box-shadow var(--dur) var(--ease)`.
- `.btn:hover` adds `box-shadow: var(--shadow-raised)`.
- `.btn:active { transform: translateY(0); }`.
- `.btn:disabled { opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; }`.
- `.btn-primary:hover` keeps deepened brand; `.btn-quiet:hover` uses `--chip` darkened via `color-mix`.
- `:focus-visible` uses `--brand` with 3px outline (already present; leave).
- Add `button, select { cursor: pointer; }`.

### Task 4: Refine header, hero and QOTD card

**Objective:** Improve hierarchy and rhythm on the highest-impact surfaces.

**Files:** Modify `assets/site.css` sections `Header` (56-88), `Hero` (130-135), `QOTD card` (137-155).

- `.site-header` background uses `color-mix(in srgb, var(--paper) 96%, transparent)`.
- `.brand-mark` uses `--brand-deep`, radius `--radius-sm`, added subtle shadow.
- `.nav a` hover/aria-current uses `--brand-tint` and `--brand`.
- `.hero` gets a soft top-to-bottom wash: `background: linear-gradient(180deg, var(--brand-tint) 0%, var(--ground) 100%)`.
- `.eyebrow` keeps accent but adds `letter-spacing: .14em`.
- `.q-card` radius becomes `--radius-lg`, shadow `var(--shadow-raised)`, padding 24px.
- `.option` min-height 50px, border `--rule`, hover border `--brand`; `.option .letter` uses `--brand-tint` and `--brand` text.
- `.verdict` colour resolves from `--ok`/`--bad` via JS classes already present.
- `.explanation` background `--brand-tint`, border-left `--brand`.

### Task 5: Refine cards, notices, forms and footer

**Objective:** Make secondary surfaces consistent with the new tokens.

**Files:** Modify `assets/site.css` sections `Stats and cards` (179-193), `Forms` (195-206), `Footer` (208-217), `Practice runner` (219-234).

- `.card`, `.stat`, `.window` use `--radius`, border `--rule`, shadow `--shadow`.
- `.notice` uses `--accent-soft`, text `color-mix(in srgb, var(--accent) 75%, var(--ink))`.
- `.field input/select/textarea` focus uses `--brand` border and a 3px `--brand-tint` ring.
- `.site-footer` stays `--brand-deep`; footer links lighten on hover.
- `.quiz-shell` uses `--radius-lg` and `var(--shadow-raised)`.
- `.result-box` uses `--brand-tint` instead of generic chip.
- `.progress > span` uses `--brand` with `--ease` transition.

### Task 6: Motion and reduced-motion

**Objective:** Ensure all animation respects accessibility preference.

**Files:** Modify `assets/site.css`.

- Add a single `@media (prefers-reduced-motion: reduce)` block setting `transition-duration: 0.01ms !important` and `animation-duration: 0.01ms !important` for all elements.
- Keep the existing marquee-specific reduced-motion rule (harmless duplication acceptable) or fold it into the new block.

### Task 7: Verify

**Objective:** Prove no regressions and no overflow.

Commands:

```bash
cd /root/emmaus-passquestions
python3 tools/build_pages.py
node --test tests/*.test.js        # 13 passed, 0 failed
node --check assets/site.js
# internal link check -> 0 broken
```

Browser checks on local preview at 390/768/1280px for home, practice, paper, maths:
- `scrollWidth <= innerWidth`
- header/hero/QOTD/practice/footer visible and readable
- quiz still answers and scores correctly

### Task 8: Publish

**Objective:** Commit CSS and rebuild Pages.

```bash
git add assets/site.css
git commit -m "style: refined institutional-blue visual polish"
git push origin main
git checkout gh-pages
git merge main
git push origin gh-pages
```

Verify `https://rhemabwoy28.github.io/emmaus-passquestions/` returns 200 and reflects the new CSS.
