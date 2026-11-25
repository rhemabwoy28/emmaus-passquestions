# Emmaus site visual polish — design

Date: 2026-11-25
Status: approved by direction selection; detailed confirmation timed out, proceeding with recommended token-level scope.

## Goal

Refresh the visual polish of all 98 static pages without changing behaviour, markup, or copy. Direction: **A — refined institutional blue**, closest to the existing identity.

## Scope

- Single file: `assets/site.css`.
- No HTML, template, generator, JavaScript or content changes.
- No new dependencies, fonts, images or network requests.

## Approach

Token-level refinement (recommended of three options considered). Retune the design tokens and migrate hard-coded component values onto them; lightly clean up component rules where values are duplicated.

## Token changes

- Brand ramp: keep `#1a5c8c` as primary; deepen dark states, add a subtle tint token for hero/selected surfaces.
- Neutral ramp: warmer, slightly cooler greys with clearer `--ink`, `--ink-600`, `--ink-400` separation.
- Accent: retain terracotta `#c2410c` for eyebrows/notices only.
- Radius scale: small (10px), medium (14px), large (20px).
- Shadow scale: subtle card shadow, raised hover shadow.
- Type scale: documented step for eyebrow, small, body, lead, h3, h2, h1.
- Motion: one shared ease/duration; all transitions respect `prefers-reduced-motion`.

## Component changes

Header, buttons/pills, hero, QOTD and practice cards, options, verdicts/explanations, notices, stats, list/table rows, forms and footer receive consistent spacing, border colours and hover/focus/disabled states. Touch targets remain at least 44px. No layout structure changes.

## Error handling

None required; no new logic.

## Testing

1. `python3 tools/build_pages.py` produces byte-identical HTML (no template changes).
2. Existing `node --test tests/*.test.js` stays green (13 tests).
3. Internal link check reports zero broken links.
4. Browser checks at 390px, 768px and 1280px: no horizontal overflow; header, hero, QOTD card, practice runner and footer readable.
5. Rebuild and verify GitHub Pages reflects the CSS change.

## Out of scope

- New pages, sections, content rewrites, or images.
- Changing the quiz engine or question bank.
- Adding a custom domain, analytics or fonts.
