/* Emmaus static replica — vanilla interactions, no network calls. */
(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* Theme: pre-paint script in <head> applies the stored class; this keeps UI in sync. */
  const syncThemeButton = () => {
    const btn = $('[data-theme-toggle]');
    if (!btn) return;
    const dark = document.documentElement.classList.contains('dark');
    btn.setAttribute('aria-pressed', String(dark));
    btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    const label = $('[data-theme-label]', btn);
    if (label) label.textContent = dark ? 'Light' : 'Dark';
  };
  document.addEventListener('DOMContentLoaded', () => {
    syncThemeButton();
    $('[data-theme-toggle]')?.addEventListener('click', () => {
      const dark = document.documentElement.classList.toggle('dark');
      try { localStorage.setItem('emmaus:theme', dark ? 'dark' : 'light'); } catch (_) {}
      syncThemeButton();
    });
  });

  /* Mobile menu */
  document.addEventListener('DOMContentLoaded', () => {
    const toggle = $('[data-menu-toggle]');
    const menu = $('[data-mobile-nav]');
    toggle?.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    $$('[data-mobile-nav] a').forEach(a => a.addEventListener('click', () => {
      menu.classList.remove('open');
      toggle?.setAttribute('aria-expanded', 'false');
    }));
  });

  /* Question of the day: client-side grading, explanation first, then gate. */
  document.addEventListener('DOMContentLoaded', () => {
    const quiz = $('[data-quiz]');
    if (!quiz) return;
    const options = $$('[data-correct]', quiz);
    const verdict = $('[data-verdict]', quiz);
    const explanation = $('[data-explanation]', quiz);
    const gate = $('[data-gate]', quiz);
    options.forEach(btn => btn.addEventListener('click', () => {
      if (quiz.dataset.done === '1') return;
      quiz.dataset.done = '1';
      const right = btn.dataset.correct === 'true';
      options.forEach(o => {
        o.disabled = true;
        o.setAttribute('aria-disabled', 'true');
        const correct = o.dataset.correct === 'true';
        o.classList.toggle('correct', correct);
        o.classList.toggle('wrong', !correct && o === btn);
        o.classList.toggle('dim', !correct && o !== btn);
      });
      if (verdict) {
        verdict.textContent = right ? 'Correct — well done.' : "Not quite. Here's the working.";
        verdict.classList.remove('hidden');
        quiz.setAttribute('aria-live', 'polite');
      }
      explanation?.classList.remove('hidden');
      gate?.classList.remove('hidden');
    }));
  });

  /* Level tabs (visual only in the static build). */
  document.addEventListener('DOMContentLoaded', () => {
    const tabs = $$('[data-tab]');
    if (!tabs.length) return;
    const select = name => {
      tabs.forEach(t => t.setAttribute('aria-selected', String(t.dataset.tab === name)));
      $$('[data-panel]').forEach(p => p.classList.toggle('hidden', p.dataset.panel !== name));
    };
    tabs.forEach(t => t.addEventListener('click', () => select(t.dataset.tab)));
  });

  /* Marquee pause/play */
  document.addEventListener('DOMContentLoaded', () => {
    const band = $('[data-marquee]');
    const btn = $('[data-marquee-toggle]');
    btn?.addEventListener('click', () => {
      const paused = band.classList.toggle('paused');
      btn.textContent = paused ? 'Play' : 'Pause';
      btn.setAttribute('aria-pressed', String(paused));
    });
  });

  /* Local search across generated paper/topic links. */
  document.addEventListener('DOMContentLoaded', () => {
    const form = $('[data-search-form]');
    if (!form) return;
    const input = $('[data-search-input]', form);
    const results = $('[data-search-results]');
    const render = () => {
      const q = (input?.value || '').trim().toLowerCase();
      if (!results) return;
      if (!q) { results.innerHTML = '<p class="muted">Type a year, topic or paper to search.</p>'; return; }
      const links = $$('[data-searchable]');
      const hits = links.filter(a => (a.dataset.searchable || a.textContent || '').toLowerCase().includes(q));
      results.innerHTML = hits.length
        ? `<ul class="list">${hits.slice(0, 30).map(a => `<li><a href="${a.getAttribute('href')}">${a.textContent.trim()}</a><span class="muted small">${a.dataset.kind || ''}</span></li>`).join('')}</ul>`
        : '<p class="muted">No matches in this offline demo.</p>';
    };
    form.addEventListener('submit', e => { e.preventDefault(); render(); });
    input?.addEventListener('input', render);
    render();
  });

  /* Sign-in form is deliberately inert in the static build. */
  document.addEventListener('DOMContentLoaded', () => {
    const form = $('[data-demo-form]');
    form?.addEventListener('submit', e => {
      e.preventDefault();
      const toast = document.createElement('div');
      toast.className = 'toast';
      toast.textContent = 'Accounts are not enabled in this static demo.';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 2600);
    });
  });
})();
