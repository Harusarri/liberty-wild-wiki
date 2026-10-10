#!/usr/bin/env python3
"""Build the complete static wiki. Python 3.13+, no network or package install."""
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/markdown2'))
import markdown2

OUT = ROOT / 'dist'
DOMAIN = 'https://wiki.libertywild.org'
DATE = '2026-10-10'
CATEGORIES = [
    ('처음 오셨나요', '시작하기', 'compass', '첫 접속부터 꼭 알아둘 기능까지', '#f0f1ea', '#7a8667'),
    ('요리와 농사', '요리와 농사', 'utensils', '새로운 작물로 채우는 나만의 식탁', '#f7efe6', '#b0865d'),
    ('거래와 보호', '거래와 보호', 'shield-check', '내 공간을 지키고 이웃과 거래하기', '#edf1f5', '#788fa8'),
    ('생존과 생활', '생존과 생활', 'pickaxe', '모험을 조금 더 편하게 만드는 기능', '#f2eeea', '#9b8371'),
    ('건축과 꾸미기', '건축과 꾸미기', 'paintbrush', '작은 소품부터 함께 만드는 마을까지', '#f2edf3', '#a18aa5'),
    ('음악과 소통', '음악과 소통', 'music-2', '목소리와 음악으로 가까워지는 시간', '#edf2ed', '#80957c'),
]
CAT = {c[0]: c for c in CATEGORIES}
pages = []
for f in sorted((ROOT / 'content').glob('*.json')):
    pages.extend(json.loads(f.read_text()))
pages.sort(key=lambda p: (list(CAT).index(p['category']), p['order'], p['slug']))
assert len({p['slug'] for p in pages}) == len(pages), 'Duplicate slug'
assert all(re.fullmatch(r'[a-z0-9-]+', p['slug']) for p in pages)
assert all('verified_notes' not in p for p in pages), 'Internal research must not be public'
PAGES = {p['slug']: p for p in pages}
all_text = json.dumps(pages, ensure_ascii=False)
for link in re.findall(r'\]\(/guide/([a-z0-9-]+)/', all_text):
    assert link in PAGES, f'Broken guide link: {link}'

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / 'assets').mkdir(parents=True)

def asset(name, data):
    if isinstance(data, str):
        data = data.encode()
    stem, ext = name.rsplit('.', 1)
    hashed = f'assets/{stem}.{hashlib.sha256(data).hexdigest()[:12]}.{ext}'
    (OUT / hashed).write_bytes(data)
    return hashed

CSS = asset('site.css', (ROOT / 'assets/site.css').read_bytes())
JS = asset('site.js', (ROOT / 'assets/site.js').read_bytes())
symbols = []
for f in sorted((ROOT / 'vendor/lucide/icons').glob('*.svg')):
    body = re.sub(r'<svg\b[^>]*>|</svg>', '', f.read_text()).strip()
    symbols.append(f'<symbol id="{f.stem}" viewBox="0 0 24 24">{body}</symbol>')
ICONS = asset('icons.svg', '<svg xmlns="http://www.w3.org/2000/svg">' + ''.join(symbols) + '</svg>')
ITEM_ICONS = {f.name:asset('item-'+f.name, f.read_bytes()) for f in sorted((ROOT/'assets/item-icons').glob('*.png'))}
DIAGRAMS = {f.name:asset(f.name, f.read_bytes()) for f in sorted((ROOT/'assets/diagrams').glob('*.svg'))}
FAVICON = ITEM_ICONS['minecraft-book.png']
ITEM_MAP = {
 'book-open':'minecraft-book.png', 'compass':'minecraft-compass_16.png',
 'utensils':'farmersdelight-cooking_pot.png', 'shield-check':'minecraft-iron_chestplate.png',
 'pickaxe':'minecraft-iron_pickaxe.png', 'paintbrush':'minecraft-painting.png',
 'music-2':'minecraft-music_disc_cat.png', 'leaf':'minecraft-wheat.png',
 'house':'minecraft-oak_sign.png', 'volume-2':'minecraft-goat_horn.png',
 'store':'minecraft-emerald.png', 'map':'minecraft-filled_map.png',
}
PHOTOS = {}
if (ROOT/'media/photos.json').exists():
    PHOTOS = json.loads((ROOT/'media/photos.json').read_text())
    for photo in PHOTOS.values():
        for variant in photo['variants']:
            variant['asset'] = asset('photo-'+variant['file'], (ROOT/'media'/variant['file']).read_bytes())

def plain(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text)).strip()

search = []
rendered = {}
for p in pages:
    body = str(markdown2.markdown(p['body_markdown'], extras=['tables', 'fenced-code-blocks', 'strike']))
    search_extra = ' '.join(x.get('caption','') for x in p.get('visual_steps',[])) + ' '.join(x.get('body_markdown','') for x in p.get('details',[]))
    toc = []
    def heading(m):
        title = plain(m[1])
        anchor = 'section-' + str(len(toc) + 1)
        toc.append((anchor, title))
        return f'<h2 id="{anchor}">{m[1]}</h2>'
    body = re.sub(r'<h2>(.*?)</h2>', heading, body)
    body = body.replace('<table>', '<div class="table-wrap" tabindex="0" role="region" aria-label="안내 표"><table>').replace('</table>', '</table></div>')
    rendered[p['slug']] = (body, toc)
    search.append({k:p[k] for k in ['title','summary','category']} | {'path': f'guide/{p["slug"]}/', 'text':html.unescape(plain(body+' '+search_extra))})
SEARCH = asset('search.json', json.dumps(search, ensure_ascii=False, separators=(',',':')))
E = html.escape

def icon(name, base):
    if name in ITEM_MAP:
        return f'<img class="icon item-icon" src="{base}{ITEM_ICONS[ITEM_MAP[name]]}" width="32" height="32" alt="" aria-hidden="true" decoding="async">'
    return f'<svg class="icon" aria-hidden="true"><use href="{base}{ICONS}#{name}"></use></svg>'

def sidebar(active, category, base):
    groups = []
    for name, label, ico, *_ in CATEGORIES:
        entries = [p for p in pages if p['category'] == name]
        links = ''.join(f'<a class="nav-link{" active" if p["slug"] == active else ""}" {"aria-current=\"page\"" if p["slug"] == active else ""} href="{base}guide/{p["slug"]}/">{E(p["title"])}</a>' for p in entries)
        groups.append(f'<details class="nav-group" {"open" if category == name or (not category and name == "처음 오셨나요") else ""}><summary><span class="nav-category">{icon(ico,base)}{label}</span>{icon("chevron-down",base)}</summary>{links}</details>')
    return f'''<aside class="sidebar" aria-label="문서 탐색">
<a class="brand" href="{base}"><span class="brandmark">{icon('book-open',base)}</span><span><strong>LIBERTY WILD</strong><small>우리의 야생 생활 안내서</small></span></a>
<button type="button" class="icon-button mobile-close" data-close-menu aria-label="목차 닫기">{icon('x',base)}</button>
<button type="button" class="search-trigger" data-search>{icon('search',base)}<span>궁금한 내용 검색</span><kbd>⌘ K</kbd></button>
<nav class="nav-scroll"><a class="nav-link{' active' if active == 'home' else ''}" href="{base}">{icon('house',base)}위키 홈</a><a class="nav-link{' active' if active == 'guides' else ''}" href="{base}guides/">{icon('book-open',base)}전체 문서</a>{''.join(groups)}</nav>
<div class="sidebar-bottom"><span class="status-dot"></span>함께 만들어 가는 리버티 와일드</div></aside>'''

def footer(base):
    return f'<footer class="footer"><span>LIBERTY WILD WIKI · {len(pages)}개의 생활 안내</span><span><a href="{base}about/">위키 안내 · 출처</a> &nbsp; / &nbsp; 2026.10 기준</span></footer>'

def layout(title, summary, path, content, active='', category='', wide=False):
    base = '../' * len([x for x in path.split('/') if x]) or './'
    full_title = title + ' · 리버티 와일드 위키' if active != 'home' else '리버티 와일드 위키 · 우리의 야생 생활 안내서'
    crumb = '위키 홈' if active == 'home' else category or title
    return f'''<!doctype html>
<html lang="ko" data-base="{base}" data-search="{SEARCH}" data-icons="{base}{ICONS}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f9f8f7"><title>{E(full_title)}</title><meta name="description" content="{E(summary)}"><link rel="canonical" href="{DOMAIN}/{path}"><meta property="og:type" content="website"><meta property="og:locale" content="ko_KR"><meta property="og:title" content="{E(full_title)}"><meta property="og:description" content="{E(summary)}"><meta property="og:url" content="{DOMAIN}/{path}"><link rel="icon" type="image/png" href="{base}{FAVICON}"><link rel="stylesheet" href="{base}{CSS}"><script defer src="{base}{JS}"></script><style>.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}</style><noscript><style>@media(max-width:760px){{.sidebar{{position:static;transform:none;width:100%;max-height:320px}}.brand,.sidebar-bottom,.search-trigger,.menu-toggle{{display:none}}.nav-scroll{{overflow:auto}}}}button[data-search]{{display:none}}</style></noscript></head>
<body><a class="skip" href="#main">본문으로 건너뛰기</a>{sidebar(active,category,base)}<button class="backdrop" data-close-menu aria-label="목차 닫기" tabindex="-1"></button>
<div class="shell"><header class="topbar"><button class="icon-button menu-toggle" aria-label="목차 열기" aria-expanded="false">{icon('menu',base)}</button><div class="breadcrumb"><a href="{base}">리버티 와일드</a>{icon('chevron-right',base)}<span>{E(crumb)}</span></div><nav class="top-links" aria-label="바로가기"><a href="{base}guide/getting-started/">처음 오셨나요?</a><a href="https://map.libertywild.org" target="_blank" rel="noopener">서버 지도 {icon('arrow-up-right',base)}</a></nav></header>
<main id="main" class="main" tabindex="-1">{content}{footer(base)}</main></div>
<dialog id="search-dialog" aria-label="위키 검색"><form method="dialog" class="search-head">{icon('search',base)}<label for="search-input" class="sr-only">검색어</label><input id="search-input" type="search" placeholder="무덤, 냄비, 구역… 무엇이 궁금하세요?" autocomplete="off"><button type="button" class="icon-button" data-close-search aria-label="검색 닫기">{icon('x',base)}</button></form><div id="search-results" class="search-results" aria-live="polite"><p class="search-hint">제목과 본문을 함께 검색합니다.</p></div><div class="search-foot">↑ ↓ 이동 &nbsp; Enter 열기 &nbsp; Esc 닫기</div></dialog><span id="copy-status" class="sr-only" role="status"></span></body></html>'''

def write(path, text):
    f = OUT / path
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(text)

def quick(slug, ico, label, base='./'):
    return f'<a class="quick-link" href="{base}guide/{slug}/">{icon(ico,base)}<span>{label}</span>{icon("arrow-right",base)}</a>'

cards = []
for name,label,ico,description,tone,tint in CATEGORIES:
    count = sum(p['category'] == name for p in pages)
    first = next(p for p in pages if p['category'] == name)
    cards.append(f'<a class="category-card" href="./guides/#{CATEGORIES.index(CAT[name])+1}" style="--tone:{tone};--tint:{tint}"><span class="tile-icon">{icon(ico,"./")}</span><h3>{label}</h3><p>{description}</p><div class="card-bottom"><span>{count}개의 안내</span>{icon("arrow-right","./")}</div></a>')
home = f'''<section class="hero"><div class="page-icon">{icon('book-open','./')}</div><div class="eyebrow">사진으로 배우는 리버티 와일드</div><h1>우리의 야생 생활 안내서</h1><p class="lead">처음 만나는 음식부터, 함께 만드는 마을까지.<br>리버티 와일드의 새로운 일상을 차근차근 알아보세요.</p></section>
<a class="welcome-note" href="./guide/getting-started/">{icon('leaf','./')}<div><strong>처음 오셨다면, 여기서 시작해요.</strong><p>첫 접속 준비와 알아두면 편한 기능을 한 페이지에 모았어요. &nbsp; →</p></div></a>
<section><div class="section-heading"><h2>어떤 생활을 시작해 볼까요?</h2><a href="./guides/">전체 문서 보기 →</a></div><div class="card-grid">{''.join(cards)}</div></section>
<section><div class="section-heading"><h2>자주 찾는 안내</h2><span>필요한 순간, 빠르게</span></div><div class="quick-grid">{quick('graves','compass','죽었을 때 물품 되찾기')}{quick('recipe-search','search','아이템 만드는 법 찾기')}{quick('claims','shield-check','내 집과 상자 보호하기')}{quick('voice-chat','volume-2','친구와 음성 대화 시작하기')}{quick('first-kitchen','utensils','나만의 첫 주방 만들기')}{quick('shops','store','가게를 열고 물건 팔기')}</div></section>'''
write('index.html', layout('위키 홈','리버티 와일드 서버의 요리, 농사, 보호, 거래, 건축, 음악을 배우는 쉬운 한국어 안내서.','',home,'home'))

def md(text,base='../../'):
    result = str(markdown2.markdown(text, extras=['tables','fenced-code-blocks']))
    result = re.sub(r'href="/(?!/)', f'href="{base}', result)
    return result.replace('<table>','<div class="table-wrap" tabindex="0" role="region" aria-label="안내 표"><table>').replace('</table>','</table></div>')

def photo_figure(name,base,markers=None,caption=None):
    photo=PHOTOS[name];variants=sorted(photo['variants'],key=lambda v:v['width']);full=base+variants[-1]['asset']
    iw,ih=photo.get('width',1600),photo.get('height',900)
    x,y,w,h=photo.get('focus',[0,0,iw,ih])
    assert w>0 and h>0 and x>=0 and y>=0 and x+w<=iw and y+h<=ih, name
    crop=(x,y,w,h)!=(0,0,iw,ih)
    imgstyle=f'width:{iw/w*100:.5f}%;max-width:none;left:{-x/w*100:.5f}%;top:{-y/h*100:.5f}%;' if crop else 'width:100%;left:0;top:0;'
    srcset='' if crop else ' srcset="'+', '.join(f'{base}{v["asset"]} {v["width"]}w' for v in variants)+'" sizes="(max-width:760px) calc(100vw - 44px), 760px"'
    points='';legend=''
    for i,m in enumerate(markers or [],1):
        px=(m['x']-x)/w*100;py=(m['y']-y)/h*100
        assert 0<=px<=100 and 0<=py<=100, (name,m)
        points+=f'<span class="photo-marker" style="left:{px:.2f}%;top:{py:.2f}%" aria-hidden="true">{i}</span>'
        legend+=f'<span><b>{i}</b> {E(m["label"])}</span>'
    legends=f'<div class="photo-legend">{legend}</div>' if legend else ''
    source_note={'website':'공개 웹 지도 화면','community':'자료실 원문 화면'}.get(photo.get('kind'),'실제 게임 화면')
    credit=f' · <a href="{E(photo["source_url"])}" target="_blank" rel="noopener">포럼 원문</a>' if photo.get('source_url') else ''
    return f'<figure class="guide-photo"><a class="photo-frame" style="aspect-ratio:{w}/{h}" href="{full}" target="_blank" rel="noopener" aria-label="{E(photo["alt"])} — 사진 크게 보기"><img style="{imgstyle}" src="{full}"{srcset} width="{iw}" height="{ih}" alt="{E(photo["alt"])}" loading="lazy" decoding="async">{points}</a>{legends}<figcaption>{E(caption or photo["caption"])}<small>{source_note} · 눌러서 크게 보기{credit}</small></figcaption></figure>'

def diagram_figure(name,base):
    return f'<figure class="guide-diagram"><img src="{base}{DIAGRAMS[name]}" alt="중계기 바로 위에 장거리 안테나를 설치하고 양쪽 안테나의 주파수를 맞추는 배치도. 감지체 사이 높이 차이는 17블록 이상이며 X와 Z가 같아야 합니다." width="680" height="680" loading="lazy"><figcaption>장거리 연결 배치도 · 두 장치의 위쪽 감지체를 기준으로 높이를 셉니다.</figcaption></figure>'


for p in pages:
    base = '../../'
    body, toc = rendered[p['slug']]
    body = re.sub(r'href="/(?!/)', f'href="{base}', body)
    related = [x for x in pages if x['category'] == p['category'] and x['slug'] != p['slug']][:3]
    references = ''.join(f'<li><a href="{E(s["url"])}" target="_blank" rel="noopener">{E(s["title"])}</a></li>' for s in p.get('sources',[]))
    sources = f'<details class="sources"><summary>이 문서의 참고 자료</summary><ul>{references}</ul><p>기능별로 운영 설정, 제작자 문서와 서버 자료실을 확인했습니다. 버전이 다른 자료는 현재 화면과 차이가 있을 수 있습니다.</p></details>' if references else ''
    related_html = '<section class="related"><h2>이어서 읽어 보세요</h2>' + ''.join(f'<a href="../{x["slug"]}/">{E(x["title"])} →</a>' for x in related) + '</section>' if related else ''
    photos_html = ''.join(photo_figure(name,base) for name in p.get('photos',[]))
    steps_html=''
    for n,step in enumerate(p.get('visual_steps',[]),1):
        title=re.sub(r'^\d+\.\s*','',step['title'])
        toc.append(('step-'+str(n),title))
        picture=photo_figure(step['photo'],base,step.get('markers'),step.get('photo_caption')) if step.get('photo') else ''
        item=step.get('icon_asset') or p.get('icon_asset') or ITEM_MAP[CAT[p['category']][2]]
        illustration=f'<img class="step-item item-icon" src="{base}{ITEM_ICONS[item]}" alt="" width="40" height="40" decoding="async">' if not picture else ''
        steps_html+=f'<section class="visual-step" id="step-{n}"><h2><span class="step-number">{n}</span>{E(title)}</h2><div class="step-instruction">{illustration}<div>{md(step["caption"],base)}</div></div>{picture}</section>'
    details_html=''
    for detail in p.get('details',[]):
        diagram=diagram_figure(detail['diagram'],base) if detail.get('diagram') else ''
        details_html+=f'<details class="guide-detail"><summary>{E(detail["title"])}</summary><div>{diagram}{md(detail["body_markdown"],base)}</div></details>'
    visual_icon=p.get('icon_asset') or ITEM_MAP[CAT[p['category']][2]]
    header_icon=f'<img class="article-item item-icon" src="{base}{ITEM_ICONS[visual_icon]}" alt="" width="48" height="48">'
    content = f'''<div class="article-layout"><article><header class="article-header">{header_icon}<div class="eyebrow">{E(p['category'])}</div><h1>{E(p['title'])}</h1><p class="lead">{E(p['summary'])}</p><div class="article-meta"><span>{'사진과 순서로 보기' if p.get('visual_steps') else '생활 안내'}</span><span>2026.10.10 확인</span></div></header>{photos_html}<div class="article-body">{body}{steps_html}{details_html}</div>{sources}{related_html}</article><nav class="toc" aria-label="이 문서의 목차"><div class="toc-title">이 페이지에서</div>{''.join(f'<a href="#{a}">{E(t)}</a>' for a,t in toc)}</nav></div>'''
    write(f'guide/{p["slug"]}/index.html',layout(p['title'],p['summary'],f'guide/{p["slug"]}/',content,p['slug'],p['category']))

catalog = '<div class="hero"><div class="eyebrow">아이템으로 찾는 생활 안내</div><h1>전체 문서</h1><p class="lead">궁금한 주제부터 골라 읽어도 괜찮아요.</p></div>'
for i,(name,label,*_) in enumerate(CATEGORIES,1):
    catalog += f'<section id="{i}" class="catalog-group"><h2>{label}</h2>'
    for p in pages:
        if p['category'] == name:
            catalog += f'<a class="catalog-row" href="../guide/{p["slug"]}/"><strong>{E(p["title"])}</strong><p>{E(p["summary"])}</p></a>'
    catalog += '</section>'
write('guides/index.html',layout('전체 문서','주제별로 찾아보는 리버티 와일드의 생활 안내.','guides/',catalog,'guides'))
about = '''<article class="article-body"><div class="eyebrow">위키 안내</div><h1>위키 안내와 출처</h1><p>리버티 와일드에서 처음 만나는 기능을 쉽게 익히도록 만든 안내서입니다. 2026년 10월 10일의 운영 서버 설치 파일, 제작법, 설정과 일반 사용자 권한을 확인했습니다.</p><h2>무엇을 담았나요?</h2><p>요리·농사·생활·보호·거래·꾸미기·소통처럼 플레이어가 직접 사용하는 기능을 담았습니다. 관리 도구와 성능 개선 모드는 사용법 목차에서 제외했습니다. 호환 패치는 관련 콘텐츠 설명에 반영했습니다.</p><p>문서는 설치 파일과 설정을 분석해 작성했습니다. 모든 기능을 운영 서버에서 직접 플레이하며 시험한 것은 아닙니다. 서버 업데이트와 구역별 설정에 따라 동작이 달라질 수 있으며, 제작법은 게임 안의 사전에서도 확인해 주세요.</p><h2>서버 자료실도 함께 참고합니다</h2><p>Discord 자료실의 사용 경험과 안내를 현재 설치 버전·공식 문서와 대조해 반영합니다. 문서 하단과 자료실 사진에는 원문 링크를 남기며, 원문을 열려면 Discord 로그인과 채널 접근 권한이 필요할 수 있습니다. 예전 사진은 게시 시점을 표시하여 새로 촬영한 공허 촬영장 사진과 구분합니다. 원문 대화나 개인 워프 좌표는 공개 위키에 옮기지 않습니다.</p><h2>가볍고 빠르게 읽기</h2><p>문서는 미리 만들어진 HTML로 제공됩니다. 외부 글꼴을 내려받지 않으며, 한번 방문한 문서와 화면 파일은 브라우저에 저장되어 다시 읽을 때 사용할 수 있습니다. 오프라인에서는 이미 읽은 문서만 볼 수 있습니다.</p><h2>디자인과 오픈 소스</h2><ul><li>밝은 색상과 글꼴 구성: <a href="https://github.com/diegoeis/obsidianotion">Obsidianotion</a>을 웹에 맞게 수정했습니다. Unlicense.</li><li>메뉴의 아이템 이미지: Minecraft 26.3과 Farmer’s Delight Refabricated의 실제 아이템 텍스처입니다. Minecraft 자산은 Mojang AB / Microsoft, Farmer’s Delight 자산은 해당 제작자의 권리이며 MIT 고지를 함께 보관합니다. <a href="../licenses/item-icons.json">아이템별 출처</a> · <a href="../licenses/FarmersDelight.txt">MIT 고지</a>. <a href="https://www.minecraft.net/en-us/usage-guidelines">Minecraft 사용 지침</a>.</li><li>검색·화살표 등 조작 아이콘: <a href="https://lucide.dev">Lucide</a>. ISC License.</li><li>문서 변환기: <a href="https://github.com/trentm/python-markdown2">python-markdown2</a> 2.5.3. MIT License.</li></ul><p>Minecraft 및 Notion의 공식 제품이나 제휴 사이트가 아닌 팬 안내서입니다. 각 모드와 데이터팩의 권리는 해당 제작자에게 있습니다. 개별 문서 하단에서 원본 자료를 확인할 수 있습니다.</p></article>'''
write('licenses/item-icons.json',(ROOT/'assets/item-icons/manifest.json').read_text())
write('licenses/FarmersDelight.txt',(ROOT/'assets/item-icons/LICENSE-FarmersDelight.txt').read_text())
write('about/index.html',layout('위키 안내와 출처','위키의 범위, 확인 기준과 디자인 자산의 라이선스.','about/',about))
write('offline.html',layout('연결을 기다리고 있어요','오프라인에서는 이전에 읽은 문서를 열 수 있습니다.','', '<div class="empty-state"><h1>아직 저장하지 않은 문서예요.</h1><p class="lead">인터넷에 연결한 후 다시 열어 주세요. 이전에 읽은 문서는 뒤로 가기로 돌아가 볼 수 있습니다.</p><p><a href="./">위키 홈으로 →</a></p></div>'))
# A root-relative recovery link is intentional on the custom-domain error page.
write('404.html',layout('문서를 찾을 수 없어요','주소가 바뀌었거나 문서가 존재하지 않습니다.','', '<div class="empty-state"><h1>문서를 찾을 수 없어요.</h1><p class="lead">전체 문서 목록에서 원하는 안내를 찾아보세요.</p><p><a href="/guides/">전체 문서로 →</a></p></div>').replace('href="./','href="/').replace('src="./','src="/').replace('data-base="./"','data-base="/"').replace('data-icons="./','data-icons="/'))
write('CNAME','wiki.libertywild.org\n')
write('.nojekyll','')
urls = ['', 'guides/', 'about/'] + [f'guide/{p["slug"]}/' for p in pages]
write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{DOMAIN}/{u}</loc><lastmod>{DATE}</lastmod></url>' for u in urls)+'</urlset>')
write('robots.txt',f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n')
fingerprint = hashlib.sha256(''.join(f.read_text() for f in sorted(OUT.rglob('*.html'))).encode()).hexdigest()[:12]
precache = ['./','./offline.html',f'./{CSS}',f'./{JS}',f'./{ICONS}',f'./{FAVICON}',f'./{SEARCH}'] + [f'./{path}' for path in ITEM_ICONS.values()]
precache = list(dict.fromkeys(precache))
sw = ''''use strict';
const PREFIX='liberty-wiki-';
const CACHE=PREFIX+'__VERSION__';
const PRECACHE=__PRECACHE__;
const root=new URL('./',self.location);
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(PRECACHE)));self.skipWaiting();});
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
async function trim(cache){const keys=await cache.keys();const docs=keys.filter(k=>new URL(k.url).pathname.endsWith('/')&&!PRECACHE.some(p=>new URL(p,root).href===k.url));for(const k of docs.slice(0,Math.max(0,docs.length-80)))await cache.delete(k);}
self.addEventListener('fetch',event=>{
 const req=event.request,url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==root.origin||!url.pathname.startsWith(root.pathname)||url.pathname.endsWith('/sw.js'))return;
 if(req.mode==='navigate'){
   event.respondWith((async()=>{const cache=await caches.open(CACHE),cached=await cache.match(req,{ignoreSearch:true});const fresh=fetch(req).then(async r=>{if(r.ok){await cache.put(req,r.clone());await trim(cache);}return r;});if(cached){event.waitUntil(fresh.catch(()=>{}));return cached;}try{return await fresh;}catch{const fallback=await cache.match(new URL('offline.html',root));return new Response((await fallback.text()).replace('<head>','<head><base href="'+root.href+'">'),{headers:{'Content-Type':'text/html; charset=utf-8'}});}})());
 }else if(url.pathname.startsWith(new URL('assets/',root).pathname)){
   event.respondWith(caches.open(CACHE).then(async cache=>{const cached=await cache.match(req);if(cached)return cached;const response=await fetch(req);if(response.ok)await cache.put(req,response.clone());return response;}));
 }
});
'''.replace('__VERSION__',fingerprint).replace('__PRECACHE__',json.dumps(precache))
write('sw.js',sw)
write('build-info.json',json.dumps({'content_date':DATE,'pages':len(pages),'version':fingerprint,'assets':{'css':CSS,'js':JS,'icons':ICONS,'search':SEARCH}},ensure_ascii=False,indent=2)+'\n')
print(f'Built {len(pages)} guides, {len(urls)} indexed URLs → {OUT}')
