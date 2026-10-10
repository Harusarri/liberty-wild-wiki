#!/usr/bin/env python3
"""Check generated pages, local links, asset budget and accidental private material."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import gzip
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'dist'
errors=[]
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.lang=None;self.h1=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='html':self.lang=attrs.get('lang')
        if tag=='h1':self.h1+=1
        if attrs.get('id'):self.ids.add(attrs['id'])
        for name in ('href','src'):
            if attrs.get(name):self.links.append(attrs[name])
parsed={}
for f in OUT.rglob('*.html'):
    p=Links();p.feed(f.read_text());parsed[f]=p
    if p.lang!='ko':errors.append(f'{f}: missing Korean lang')
    if p.h1!=1:errors.append(f'{f}: expected one h1, got {p.h1}')
for f,p in parsed.items():
    for value in p.links:
        url=urlsplit(value)
        if url.scheme or url.netloc:continue
        path=unquote(url.path)
        dest=(OUT/path.lstrip('/') if path.startswith('/') else f.parent/path).resolve() if path else f
        if dest.is_dir():dest=dest/'index.html'
        if not dest.is_relative_to(OUT):errors.append(f'Escaping link {f.name}: {value}')
        elif not dest.exists():errors.append(f'Missing link {f.relative_to(OUT)}: {value}')
        elif url.fragment and dest in parsed and unquote(url.fragment) not in parsed[dest].ids:errors.append(f'Missing anchor {value} in {f.relative_to(OUT)}')
# Verify SVG symbols separately; HTMLParser does not read external sprites above.
info=json.loads((OUT/'build-info.json').read_text())
# A duplicate URL makes Cache.addAll reject the entire service-worker install.
precache=json.loads(re.search(r'const PRECACHE=(\[.*?\]);',(OUT/'sw.js').read_text()).group(1))
if len(precache)!=len(set(precache)):errors.append('Duplicate service-worker precache URL')
sprite=(OUT/info['assets']['icons']).read_text()
symbols=set(re.findall(r'id="([^"]+)"',sprite))
for f,p in parsed.items():
    for value in p.links:
        if '.svg#' in value and value.split('#',1)[1] not in symbols:errors.append('Missing SVG symbol: '+value)
budgets={'css':7000,'js':4500,'icons':5000,'search':65000}
sizes={}
for key,filename in info['assets'].items():
    data=(OUT/filename).read_bytes();sizes[key]={'raw':len(data),'gzip':len(gzip.compress(data))}
    if sizes[key]['gzip']>budgets[key]:errors.append(f'{key} gzip budget exceeded: {sizes[key]}')
for f in (ROOT/'content').glob('*.json'):
    data=f.read_text()
    for pattern in (r'"verified_notes"',r'/srv/pterodactyl',r'/storage/',r'/home/container',r'(?i)jdbc:mysql',r'(?i)(?:password|api_key|secret_key)\s*[:=]',r'156\.228\.4\.'):
        if re.search(pattern,data):errors.append(f'Private-material pattern in {f.name}: {pattern}')
if errors:
    raise SystemExit('\n'.join(errors))
print(json.dumps({'html_pages':len(parsed),'guide_pages':info['pages'],'links':'passed','source_scan':'passed','assets':sizes},ensure_ascii=False,indent=2))
