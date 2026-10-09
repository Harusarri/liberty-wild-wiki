(() => {
  'use strict';
  const root = new URL(document.documentElement.dataset.base || './', document.baseURI);
  const sidebar = document.querySelector('.sidebar');
  const menuButton = document.querySelector('.menu-toggle');
  let returnFocus;
  const mobile = () => matchMedia('(max-width:760px)').matches;
  function setMenu(open) {
    document.body.classList.toggle('menu-open', open);
    menuButton?.setAttribute('aria-expanded', String(open));
    sidebar.inert = mobile() && !open;
    if (open) { returnFocus = document.activeElement; sidebar.querySelector('.mobile-close').focus(); }
    else returnFocus?.focus();
  }
  menuButton?.addEventListener('click', () => setMenu(!document.body.classList.contains('menu-open')));
  document.querySelectorAll('[data-close-menu]').forEach(e => e.addEventListener('click', () => setMenu(false)));
  matchMedia('(max-width:760px)').addEventListener('change', () => { sidebar.inert = mobile() && !document.body.classList.contains('menu-open'); });
  sidebar.inert = mobile();
  document.addEventListener('keydown', e => {
    if (!document.body.classList.contains('menu-open')) return;
    if (e.key === 'Escape') setMenu(false);
    if (e.key === 'Tab') {
      const items = [...sidebar.querySelectorAll('a,button,summary')].filter(x => x.getClientRects().length);
      const first = items[0], last = items.at(-1);
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  const dialog = document.querySelector('#search-dialog');
  const input = document.querySelector('#search-input');
  const results = document.querySelector('#search-results');
  let indexPromise;
  let index;
  let queryNumber = 0;
  const hint = message => { results.replaceChildren(Object.assign(document.createElement('p'), {className:'search-hint', textContent:message})); };
  async function loadIndex() {
    if (!indexPromise) indexPromise = fetch(new URL(document.documentElement.dataset.search, root)).then(r => { if (!r.ok) throw Error('search'); return r.json(); }).catch(e => { indexPromise = null; throw e; });
    index = await indexPromise;
    return index;
  }
  function openSearch(e) {
    e?.preventDefault();
    if (document.body.classList.contains('menu-open')) setMenu(false);
    dialog.showModal(); input.focus();
    loadIndex().then(search).catch(() => hint('검색 자료를 불러오지 못했어요. 연결을 확인하고 다시 입력해 주세요.'));
  }
  document.querySelectorAll('button[data-search]').forEach(e => e.addEventListener('click', openSearch));
  document.querySelector('[data-close-search]')?.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); } });
  document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') openSearch(e); });
  const initials = s => [...s].map(c => { const n=c.charCodeAt(0)-0xac00; return n>=0&&n<11172 ? 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'[Math.floor(n/588)] : c; }).join('');
  async function search() {
    const seq = ++queryNumber;
    const q = input.value.trim().toLowerCase();
    if (!q) { hint('예: 무덤, 냄비, 구역, 음반 · 제목과 본문을 함께 검색합니다.'); return; }
    if (!index) { try { await loadIndex(); } catch { hint('연결 후 다시 검색해 주세요. 전체 문서 목록에서도 찾을 수 있습니다.'); return; } }
    if (seq !== queryNumber) return;
    const tokens = q.split(/\s+/);
    const found = index.map(p => {
      const title=p.title.toLowerCase(), text=(p.title+' '+p.summary+' '+p.text).toLowerCase();
      const score=tokens.reduce((n,t) => n + (title.includes(t)?8:text.includes(t)?2:initials(title).includes(t)?4:0),0);
      return {p,score,match:tokens.every(t => text.includes(t)||initials(title).includes(t))};
    }).filter(x => x.match).sort((a,b) => b.score-a.score).slice(0,30);
    if (!found.length) { hint('일치하는 문서가 없어요. 짧은 단어나 아이템 이름으로 다시 찾아보세요.'); return; }
    results.replaceChildren();
    for (const {p} of found) {
      const a=Object.assign(document.createElement('a'),{className:'search-result',href:new URL(p.path,root).href});
      a.append(Object.assign(document.createElement('strong'),{textContent:p.title}), Object.assign(document.createElement('small'),{textContent:p.category+' · '+p.summary})); results.append(a);
    }
  }
  input.addEventListener('input', search);
  input.addEventListener('keydown', e => {
    if (e.key==='ArrowDown') { e.preventDefault(); results.querySelector('a')?.focus(); }
    if (e.key==='Enter') { e.preventDefault(); results.querySelector('a')?.click(); }
  });
  results.addEventListener('keydown', e => {
    const links=[...results.querySelectorAll('a')], i=links.indexOf(document.activeElement);
    if (e.key==='ArrowDown') { e.preventDefault(); links[Math.min(i+1,links.length-1)]?.focus(); }
    if (e.key==='ArrowUp') { e.preventDefault(); if(i===0)input.focus(); else links[i-1]?.focus(); }
  });
  document.querySelectorAll('.article-body code').forEach(code => {
    const value=code.textContent.trim();
    if (!value.startsWith('/') || value.includes('\n') || value.includes('→') || !navigator.clipboard) return;
    const button=document.createElement('button'); button.type='button'; button.className='copy-button'; button.setAttribute('aria-label',value+' 복사'); button.title='명령어 복사';
    button.innerHTML='<svg class="icon" aria-hidden="true"><use href="'+document.documentElement.dataset.icons+'#copy"></use></svg>';
    button.addEventListener('click',async () => { try { await navigator.clipboard.writeText(value); button.classList.add('done'); button.setAttribute('aria-label','복사 완료'); document.querySelector('#copy-status').textContent='명령어를 복사했습니다.'; setTimeout(()=>{ button.classList.remove('done'); button.setAttribute('aria-label',value+' 복사'); },1800); } catch { document.querySelector('#copy-status').textContent='복사할 수 없습니다. 명령어를 직접 선택해 주세요.'; } });
    code.after(button);
  });
  if ('serviceWorker' in navigator && (location.protocol==='https:' || location.hostname==='localhost' || location.hostname==='127.0.0.1')) {
    addEventListener('load', () => navigator.serviceWorker.register(new URL('sw.js',root),{scope:root.pathname}).catch(()=>{}));
  }
})();
