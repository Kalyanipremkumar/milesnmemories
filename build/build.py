#!/usr/bin/env python3
"""Builds the static site for milesnmemories.travel.

Source of truth for the Rajasthan writing: src/rajasthan.html (never edited by this script).
Source for the original homepage wording: src/home-original.html.
Run from the repo root:  python3 build/build.py
"""
import json, os, re, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://milesnmemories.travel"
TODAY = "2026-10-27"
PUBLISHED = "2026-10-27"   # date the day articles were published as separate pages
AUTHOR = {"@type": "Person", "name": "Kalyani", "url": SITE + "/about/",
          "sameAs": ["https://www.instagram.com/kalyanidarimisetty/", "https://www.facebook.com/kalyani.darimisetty/"]}

def read(p): return open(os.path.join(ROOT, p), encoding="utf-8").read()
def write(p, s):
    full = os.path.join(ROOT, p); os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(s)

SRC = read("src/rajasthan.html")
HOME = read("src/home-original.html")
ARTICLE = SRC.split("<article>", 1)[1].split("</article>", 1)[0]

# Draft stories are built (noindex, with a draft banner) only while INCLUDE_DRAFTS is True.
# Set it to False before publishing the site if any story is still a draft.
INCLUDE_DRAFTS = False

# ---------------------------------------------------------------- navigation
# Two-level header (Oct 2026). Same URLs as before; dropdowns only group existing pages.
MENU = [("/", "Home", None),
        (None, "Travel Diaries", [("/travel-diaries/rajasthan/", "Rajasthan Diaries"), ("/travel-diaries/", "All Destinations"),
                                  ("/travel-notes/", "Travel Notes")]),
        (None, "Discover", [("/art-heritage/", "Art &amp; Heritage"), ("/temples-traditions/", "Temples &amp; Traditions"),
                            ("/stories-behind-the-stones/", "Stories Behind the Stones")]),
        ("/about/", "About", None), ("/contact/", "Contact", None)]

def _is_active(item_url, path):
    if item_url == "/": return path == "/"
    if item_url == "/travel-diaries/": return path == "/travel-diaries/"
    return path.startswith(item_url)

SEARCH_SVG = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6.5" '
              'fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>')

def header(path):
    cur = ' aria-current="page"'
    items = []
    for k, (url, label, kids) in enumerate(MENU):
        if kids:  # hide Stories Behind the Stones until at least one story is built
            kids = [(u, t) for u, t in kids if u != "/stories-behind-the-stones/" or STORIES]
        if kids is None:
            items.append(f'<li><a class="mh-link" href="{url}"{cur if _is_active(url, path) else ""}>{label}</a></li>')
        else:
            on = any(_is_active(u, path) for u, _ in kids)
            sub = "".join(f'<li><a href="{u}"{cur if _is_active(u, path) else ""}>{t}</a></li>' for u, t in kids)
            items.append(f'<li class="mh-dd{" is-active" if on else ""}"><button type="button" class="mh-link mh-dd-btn" aria-expanded="false" '
                         f'aria-controls="mh-sub-{k}">{label}<span class="mh-caret" aria-hidden="true"></span></button>'
                         f'<ul class="mh-sub" id="mh-sub-{k}">{sub}</ul></li>')
    return f"""<a class="skip-link" href="#main">Skip to content</a>
<header class="mh">
  <div class="mh-brand">
    <a class="mh-logo" href="/" aria-label="Miles &amp; Memories, home"><img src="/brand/logo-compact.svg" width="261" height="42" alt="Miles &amp; Memories"></a>
    <p class="mh-tag">Heritage · Culture · Journeys</p>
  </div>
  <div class="mh-bar">
    <a class="mh-logo-sm" href="/" aria-label="Miles &amp; Memories, home"><img src="/brand/logo-compact.svg" width="174" height="28" alt="Miles &amp; Memories"></a>
    <nav class="mh-nav" id="mh-nav" aria-label="Main">
      <ul class="mh-menu">{"".join(items)}</ul>
    </nav>
    <button type="button" class="mh-search-btn" aria-label="Search the journal" aria-haspopup="dialog">{SEARCH_SVG}</button>
    <button type="button" class="mh-burger" aria-expanded="false" aria-controls="mh-nav" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
</header>
<dialog class="mh-search" aria-label="Search">
  <form method="dialog" class="mh-search-form" role="search" onsubmit="return false">
    <label for="mh-q">Search Miles &amp; Memories</label>
    <div class="mh-search-row"><input id="mh-q" type="search" autocomplete="off" placeholder="Try Udaipur, frescoes, Mehrangarh…">
    <button type="button" class="mh-search-close">Close</button></div>
    <ul class="mh-results" aria-live="polite"></ul>
  </form>
</dialog>
"""

HEADER_JS = """<script>
(() => {
  const mh = document.querySelector('.mh'); if (!mh) return;
  const burger = mh.querySelector('.mh-burger'), nav = mh.querySelector('.mh-nav');
  const dds = [...mh.querySelectorAll('.mh-dd')];
  const desktop = () => matchMedia('(min-width: 900px)').matches;
  const closeAll = except => dds.forEach(d => { if (d !== except) { d.classList.remove('open'); d.querySelector('button').setAttribute('aria-expanded', 'false'); } });
  dds.forEach(d => {
    const b = d.querySelector('button');
    b.addEventListener('click', () => { const o = !d.classList.contains('open'); closeAll(d); d.classList.toggle('open', o); b.setAttribute('aria-expanded', o); });
    d.addEventListener('mouseenter', () => { if (desktop()) { closeAll(d); d.classList.add('open'); b.setAttribute('aria-expanded', 'true'); } });
    d.addEventListener('mouseleave', () => { if (desktop()) { d.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); } });
    d.addEventListener('focusout', e => { if (desktop() && !d.contains(e.relatedTarget)) { d.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); } });
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    const o = dds.find(d => d.classList.contains('open'));
    if (o) { closeAll(); o.querySelector('button').focus(); }
    else if (mh.classList.contains('menu-open')) { mh.classList.remove('menu-open'); burger.setAttribute('aria-expanded', 'false'); burger.focus(); }
  });
  document.addEventListener('click', e => { if (desktop() && !mh.contains(e.target)) closeAll(); });
  burger.addEventListener('click', () => { const o = !mh.classList.contains('menu-open'); mh.classList.toggle('menu-open', o); burger.setAttribute('aria-expanded', o); });
  // search
  const dlg = document.querySelector('dialog.mh-search'), q = dlg.querySelector('input'), out = dlg.querySelector('.mh-results');
  let idx = null;
  const esc = t => t.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const run = () => {
    const terms = q.value.toLowerCase().split(/\\s+/).filter(Boolean);
    if (!idx || !terms.length) { out.innerHTML = ''; return; }
    const score = p => terms.reduce((n, t) => n + (p.t.toLowerCase().includes(t) ? 3 : 0) + (p.d.toLowerCase().includes(t) ? 1 : 0), 0);
    const hits = idx.filter(p => terms.every(t => p.k.includes(t))).sort((a, b) => score(b) - score(a)).slice(0, 12);
    out.innerHTML = hits.length ? hits.map(p => '<li><a href="' + p.u + '"><strong>' + esc(p.t) + '</strong><span>' + esc(p.d) + '</span></a></li>').join('')
                                : '<li class="none">No matching pages yet.</li>';
  };
  mh.querySelector('.mh-search-btn').addEventListener('click', () => {
    dlg.showModal(); q.focus();
    if (!idx) fetch('/search-index.json').then(r => r.json()).then(j => { idx = j.map(p => ({...p, k: (p.t + ' ' + p.d + ' ' + p.x).toLowerCase()})); run(); }).catch(() => {});
  });
  q.addEventListener('input', run);
  dlg.querySelector('.mh-search-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
})();
</script>
"""

SEARCH_INDEX = []

WHATSAPP = "https://wa.me/919980154461"
INSTAGRAM = "https://www.instagram.com/kalyanidarimisetty/"
FACEBOOK = "https://www.facebook.com/kalyani.darimisetty/"
ICONS = {
    "whatsapp": '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 2.2A9.7 9.7 0 0 0 3.7 16.9L2.3 21.7l4.9-1.3A9.7 9.7 0 1 0 12 2.2Zm0 17.7a8 8 0 0 1-4.1-1.1l-.3-.2-2.9.8.8-2.8-.2-.3A8 8 0 1 1 12 19.9Zm4.4-6c-.2-.1-1.4-.7-1.7-.8-.2-.1-.4-.1-.5.1l-.8 1c-.1.2-.3.2-.5.1a6.6 6.6 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.5-.4h-.5a.9.9 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1 4.9 4.9 0 0 0 1 2.6 11.2 11.2 0 0 0 4.3 3.8c1.6.7 2.2.7 3 .6a2.6 2.6 0 0 0 1.7-1.2 2.1 2.1 0 0 0 .1-1.2c0-.2-.2-.2-.5-.3Z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.3" cy="6.7" r="1.2" fill="currentColor"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path fill="currentColor" d="M13.5 21.5v-8h2.7l.4-3.2h-3.1V8.3c0-.9.3-1.5 1.6-1.5h1.6V4a22 22 0 0 0-2.4-.1c-2.4 0-4 1.4-4 4.1v2.3H7.6v3.2h2.7v8h3.2Z"/></svg>',
    "contact": '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><rect x="3" y="5.5" width="18" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m3.8 7 8.2 6 8.2-6" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
}
FOOTER = f"""<footer class="mf">
  <div class="mf-cols">
    <div class="mf-brand">
      <a href="/" class="mf-logo" aria-label="Miles &amp; Memories, home"><img src="/brand/logo-compact-reversed.svg" width="220" height="35" alt="Miles &amp; Memories" loading="lazy"></a>
      <p class="mf-tag">Heritage · Culture · Journeys</p>
      <p class="mf-desc">Journeys through places, people and heritage. Stories worth remembering.</p>
    </div>
    <nav class="mf-col" aria-label="Explore">
      <h2>Explore</h2>
      <ul>
        <li><a href="/travel-diaries/">Travel Diaries</a></li>
        <li><a href="/art-heritage/">Art &amp; Heritage</a></li>
        <li><a href="/temples-traditions/">Temples &amp; Traditions</a></li>
        <li><a href="/stories-behind-the-stones/">Stories Behind the Stones</a></li>
        <li><a href="/travel-notes/">Travel Notes</a></li>
        <li><a href="/about/">About</a></li>
      </ul>
    </nav>
    <div class="mf-col">
      <h2>Connect</h2>
      <ul class="mf-social">
        <li><a href="{WHATSAPP}" target="_blank" rel="noopener">{ICONS["whatsapp"]}<span>Chat on WhatsApp</span></a></li>
        <li><a href="{INSTAGRAM}" target="_blank" rel="me noopener">{ICONS["instagram"]}<span>Instagram</span></a></li>
        <li><a href="{FACEBOOK}" target="_blank" rel="me noopener">{ICONS["facebook"]}<span>Facebook</span></a></li>
        <li><a href="/contact/">{ICONS["contact"]}<span>Contact</span></a></li>
      </ul>
    </div>
  </div>
  <div class="mf-bottom">
    <span>© 2026 Miles &amp; Memories. All rights reserved.</span>
    <span>milesnmemories.travel</span>
  </div>
</footer>
"""

LIGHTBOX = """<dialog class="lightbox" aria-label="Photo">
  <button class="close" type="button">Close</button>
  <img alt="">
  <p></p>
</dialog>
<script>
(() => {
  const dlg = document.querySelector('dialog.lightbox');
  if (!dlg) return;
  const big = dlg.querySelector('img'), cap = dlg.querySelector('p');
  document.querySelectorAll('.grid button, .day-photos button').forEach(b => b.addEventListener('click', () => {
    const small = b.querySelector('img');
    big.src = '/images/rajasthan/' + b.dataset.full + '.webp';
    big.alt = small.alt; cap.textContent = small.alt;
    dlg.showModal();
  }));
  dlg.querySelector('.close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
})();
</script>
"""

from urllib.parse import quote
def share(path, text):
    u = quote(SITE + path, safe=""); t = quote(html.unescape(text), safe="")
    return ('<div class="share" aria-label="Share this page"><span>Share</span>'
            f'<a href="https://wa.me/?text={t}%20{u}" target="_blank" rel="noopener">WhatsApp</a>'
            f'<a href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>'
            f'<a href="https://twitter.com/intent/tweet?url={u}&amp;text={t}" target="_blank" rel="noopener">X</a>'
            f'<button type="button" class="copy-link" data-url="{SITE + path}">Copy link</button></div>\n')

SITE_JS = """<a class="to-top" href="#top" aria-label="Back to top">↑ Top</a>
<script>
(() => {
  const t = document.querySelector('.to-top');
  const on = () => t.classList.toggle('show', window.scrollY > 1200);
  addEventListener('scroll', on, {passive: true}); on();
  document.querySelectorAll('.copy-link').forEach(b => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.dataset.url); b.textContent = 'Link copied'; }
    catch (e) { prompt('Copy this link:', b.dataset.url); }
  }));
})();
</script>
"""

# Future monetisation hook: pass disclosure=True to page() on any page with affiliate links.
DISCLOSURE = ('<aside class="disclosure prose"><p>Some links on this page are affiliate links. '
              'If you buy through them, I may earn a small commission at no extra cost to you.</p></aside>\n')

def page(path, *, title, desc, body, active, canonical=True, noindex=False, og_image=None,
         og_type="website", jsonld=(), lightbox=False, disclosure=False):
    url = SITE + path
    img = og_image or (SITE + "/images/og-rajasthan.jpg", 1200, 630, "Kalyani at the edge of Panna Meena ka Kund stepwell near Jaipur")
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{'<link rel="canonical" href="' + url + '">' if canonical else ''}
{'<meta name="robots" content="noindex, follow">' if noindex else ''}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Miles &amp; Memories">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img[0]}">
<meta property="og:image:width" content="{img[1]}">
<meta property="og:image:height" content="{img[2]}">
<meta property="og:image:alt" content="{img[3]}">
<meta name="twitter:card" content="summary_large_image">
{''.join('<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False) + '</script>' + chr(10) for j in jsonld)}<script defer src="/_vercel/insights/script.js"></script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#F8F5EE">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=Rozha+One&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
</head>
<body id="top">
"""
    head = re.sub(r"\n\n+", "\n", head)
    out = (head + header(path) + "\n<main id=\"main\">\n" + (DISCLOSURE if disclosure else "") + body + "\n</main>\n\n"
           + (LIGHTBOX if lightbox else "") + "\n" + FOOTER + SITE_JS + HEADER_JS + "</body>\n</html>\n")
    out = pictures(out)
    if not noindex or "/stories-behind-the-stones/" in path:
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S))))
        SEARCH_INDEX.append({"u": path, "t": html.unescape(re.sub(r"\s*\|.*$", "", title)), "d": html.unescape(desc), "x": text[:6000]})
    write(path.strip("/") + "/index.html" if path != "/" else "index.html", out)
    return url

# ---------------------------------------------------------------- images
IMG_RE = re.compile(r'<img src="/images/rajasthan/([a-z0-9]+?)(-sm)?\.jpg"([^>]*)>')
def pictures(s):
    def rep(m):
        name, sm, rest = m.group(1), m.group(2), m.group(3)
        base = f"/images/rajasthan/{name}"
        if sm:
            srcset = f"{base}-sm.webp"
            source = f'<source type="image/webp" srcset="{srcset}">'
        else:
            wm = re.search(r'width="(\d+)"', rest)
            w = int(wm.group(1)) if wm else 1600
            parts = [f"{base}-{v}.webp {v}w" for v in (480, 960)
                     if os.path.exists(os.path.join(ROOT, f"images/rajasthan/{name}-{v}.webp"))]
            parts.append(f"{base}.webp {w}w")
            source = (f'<source type="image/webp" srcset="{", ".join(parts)}" '
                      f'sizes="(min-width: 1140px) 1100px, 100vw">')
        return f'<picture>{source}<img src="{base}{sm or ""}.jpg"{rest}></picture>'
    return IMG_RE.sub(rep, s)

def thumb(img_id, alt):
    return f'<img src="/images/rajasthan/{img_id}-sm.jpg" alt="{alt}" loading="lazy">'

# ---------------------------------------------------------------- Rajasthan source slicing
MARKERS = [f"<!-- DAY {n} -->" for n in range(1, 12)] + ["<!-- REFLECTIONS -->"]
def between(a, b): return ARTICLE.split(a, 1)[1].split(b, 1)[0]

# Chapter titles chosen by Kalyani (Oct 2026 brief). The original day headings stay as subtitles.
CHAPTERS = [("day-1-jaipur-pink-city", "Jaipur: The Pink City"),
            ("day-2-jaipur-forts-panna-meena-ka-kund", "Jaipur: Forts and Panna Meena ka Kund"),
            ("day-3-mandawa-pushkar", "Mandawa and Pushkar"),
            ("day-4-pushkar-bikaner", "Pushkar and Bikaner"),
            ("day-5-jaisalmer-golden-city", "Jaisalmer: The Golden City"),
            ("day-6-jaisalmer-khuri-desert", "Jaisalmer and Khuri Desert"),
            ("day-7-jodhpur-blue-city", "Jodhpur: The Blue City"),
            ("day-8-ranakpur-kumbhalgarh", "Ranakpur and Kumbhalgarh"),
            ("day-9-nathdwara-eklingji-udaipur", "Nathdwara, Eklingji and Udaipur"),
            ("day-10-udaipur-art-heritage-markets", "Udaipur: Art, Heritage and Markets"),
            ("day-11-journey-home", "The Journey Home")]
SLUGS = [c[0] for c in CHAPTERS]
# Hero photo per chapter: the first feature photo of the day (moved up, not duplicated);
# Day 3 has no photo group, so it uses a Mandawa haveli room from the original gallery.
HERO_FALLBACK = {3: ("r06", "A Mandawa haveli room painted on every wall and ceiling", False), 11: ("h01", "Kalyani and Prem back at Bengaluru airport", True)}
COLL = "/travel-diaries/rajasthan/"
COMPLETE = COLL + "complete/"

def strip_tags(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

DAYS = []
for i in range(11):
    chunk = between(MARKERS[i], MARKERS[i + 1])
    date_ = re.search(r'<p class="date">(.*?)</p>', chunk).group(1)
    h2 = re.search(r"<h2>(.*?)</h2>", chunk).group(1)
    sub = re.search(r'<p class="sub">(.*?)</p>', chunk).group(1)
    first = re.search(r'data-full="([a-z0-9]+)"', chunk) or re.search(r'/images/rajasthan/([a-z0-9]+?)(?:-sm)?\.jpg', chunk)
    img_id = first.group(1)
    alt_m = re.search(r'data-full="%s"[^>]*?alt="([^"]*)"' % img_id, chunk) or re.search(r'alt="([^"]*)"', chunk)
    from PIL import Image
    w, h = Image.open(os.path.join(ROOT, f"images/rajasthan/{img_id}.jpg")).size
    n = i + 1
    hero_btn = re.search(r'\s*<button class="feature" data-full="([a-z0-9]+)"[^\n]*?alt="([^"]*)"[^\n]*</button>', chunk)
    if n in HERO_FALLBACK:
        hid, halt, move_solo = HERO_FALLBACK[n]
        if move_solo:
            capm = re.search(r'<figure class="wide solo">\s*<img src="/images/rajasthan/%s\.jpg".*?<figcaption>(.*?)</figcaption>' % hid, chunk, re.S)
            hero_cap = capm.group(1) if capm else ""
            chunk = re.sub(r'\s*<figure class="wide solo">\s*<img src="/images/rajasthan/%s\.jpg".*?</figure>' % hid, "", chunk, count=1, flags=re.S)
    else:
        hid, halt = hero_btn.group(1), hero_btn.group(2)
        chunk = chunk.replace(hero_btn.group(0), "", 1)
    hero_cap = locals().get("hero_cap", "") if n in HERO_FALLBACK and HERO_FALLBACK[n][2] else ""
    hw, hh = Image.open(os.path.join(ROOT, f"images/rajasthan/{hid}.jpg")).size
    DAYS.append(dict(n=n, slug=SLUGS[i], url=COLL + SLUGS[i] + "/", chunk=chunk, date=date_, h2=h2,
                     title=CHAPTERS[i][1], cap=hero_cap, sub=sub, img=hid, alt=halt, w=hw, h=hh))

def day_card(d, heading="h3"):
    return (f'<a class="story-card" href="{d["url"]}">\n  {thumb(d["img"], d["alt"])}\n  <div>\n'
            f'    <p class="when">{d["date"]}</p>\n    <{heading}>Day {d["n"]} — {d["title"]}</{heading}>\n'
            f'    <p>{d["sub"]}</p>\n    <span class="read">Read Day {d["n"]} →</span>\n  </div>\n</a>\n')

def crumbs(items):
    vis = " <span aria-hidden=\"true\">/</span> ".join(
        f'<a href="{u}">{t}</a>' if u else f'<span aria-current="page">{t}</span>' for u, t in items)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": k + 1, "name": strip_tags(t), **({"item": SITE + u} if u else {})}
        for k, (u, t) in enumerate(items)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb">{vis}</nav>\n', ld

HERO = re.search(r'<header class="story-hero">.*?</header>', ARTICLE, re.S).group(0)
ROUTE = re.search(r'<section class="route".*?</section>', ARTICLE, re.S).group(0)
INTRO = re.search(r'<div class="prose intro">.*?</div>', ARTICLE, re.S).group(0)
REFLECT_ON = ARTICLE.split("<!-- REFLECTIONS -->", 1)[1]
GLOSSARY = between("<!-- GLOSSARY -->", "<!-- NOTES -->")
NOTES = between("<!-- NOTES -->", "<!-- PHOTOS -->")
DISCLAIMER = re.search(r'<p class="note">.*?</p>', INTRO).group(0)

# ---------------------------------------------------------------- Stories Behind the Stones
import yaml, markdown
STORIES_PATH = "/stories-behind-the-stones/"
def parse_fm(fm):
    """Simple front matter: 'key: value' lines; [a, b] lists. Tolerates colons inside titles."""
    meta = {}
    for line in fm.strip().splitlines():
        if ":" not in line: continue
        k, v = line.split(":", 1); v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip("'\"")
    return meta
STORIES = []
sdir = os.path.join(ROOT, "src/stories")
for fn in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
    if not fn.endswith(".md"): continue
    raw = read("src/stories/" + fn)
    _, fm, body_md = raw.split("---", 2)
    meta = parse_fm(fm)
    if not meta.get("slug") or not meta.get("diary"):
        print("skipping incomplete story", fn); continue
    body_md = body_md.split("## Notes for Kalyani", 1)[0]        # editor notes are never published
    meta["body_md"] = body_md
    meta["url"] = STORIES_PATH + meta["slug"] + "/"
    meta.setdefault("photos", []); meta.setdefault("related", []); meta.setdefault("diary_also", [])
    if meta.get("status") == "published" or INCLUDE_DRAFTS:
        STORIES.append(meta)
BY_SLUG = {m["slug"]: m for m in STORIES}
ORDER = ["maharana-pratap-and-chetak", "jai-singh-ii-and-jantar-mantar", "amer-and-the-kachwahas", "painted-havelis-of-shekhawati",
         "rao-bika-and-bikaner", "rawal-jaisal-and-jaisalmer", "rao-jodha-and-jodhpur", "ranakpur-jain-temple",
         "kumbhalgarh-and-mewar", "eklingji-king-behind-the-kings", "udai-singh-ii-and-udaipur", "shrinathji-and-pichwai"]
STORIES.sort(key=lambda m: ORDER.index(m["slug"]) if m["slug"] in ORDER else 99)
# ---------------------------------------------------------------- complete travelogue
complete_body = "<article>" + ARTICLE + "</article>\n"
complete_body = complete_body.replace(
    '<p class="dek">', f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">/</span> '
    f'<a href="/travel-diaries/">Travel Diaries</a> <span aria-hidden="true">/</span> <a href="{COLL}">Rajasthan</a></nav>\n    <p class="dek">', 1)
complete_body = complete_body.replace(
    '<nav class="toc" aria-label="Days">',
    f'<p class="prose aside">Prefer one day at a time? <a href="{COLL}">Read the diary day by day</a>.</p>\n  <nav class="toc" aria-label="Days">', 1)
complete_body = complete_body.replace("</article>", '<div class="prose">' + share(COMPLETE, "My Rajasthan Diaries, the complete travelogue") + "</div></article>", 1)
page(COMPLETE, title="My Rajasthan Diaries: the complete travelogue | Miles &amp; Memories",
     desc="All eleven days of my October 2026 Rajasthan journey on one page: forts, frescoes, temples, desert skies and stories.",
     body=complete_body, active="/travel-diaries/", noindex=True, og_type="article", lightbox=True)

# ---------------------------------------------------------------- day articles
for i, d in enumerate(DAYS):
    prev_ = DAYS[i - 1] if i else None
    next_ = DAYS[i + 1] if i < 10 else None
    cr, cr_ld = crumbs([("/", "Home"), ("/travel-diaries/", "Travel Diaries"), (COLL, "Rajasthan"), (None, f"Day {d['n']}")])
    pager = '<nav class="pager" aria-label="Previous and next day">'
    pager += (f'<a class="prev" href="{prev_["url"]}"><span>← Previous day</span>Day {prev_["n"]} — {prev_["title"]}</a>' if prev_ else '<span></span>')
    pager += (f'<a class="next" href="{next_["url"]}"><span>Next day →</span>Day {next_["n"]} — {next_["title"]}</a>' if next_ else '<span></span>')
    pager += "</nav>\n"
    chunk = d["chunk"]
    # Chapter title becomes the h1; the original day heading stays, as the subtitle (h2). The writing is untouched.
    chunk = chunk.replace('<div class="day-head">', f'<div class="day-head">\n      <h1>Day {d["n"]} — {d["title"]}</h1>', 1)
    # sub-headings get anchors for the chapter contents list
    toc_items = []
    def anchor(m):
        t = m.group(1); a = re.sub(r"[^a-z0-9]+", "-", strip_tags(t).lower()).strip("-")
        toc_items.append((a, t)); return f'<h3 id="{a}">{t}</h3>'
    chunk = re.sub(r"<h3>(.*?)</h3>", anchor, chunk)
    toc = ""
    if len(toc_items) >= 2:
        toc = ('<nav class="chapter-toc" aria-label="In this chapter"><p>In this chapter</p><ol>'
               + "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in toc_items) + "</ol></nav>\n")
    chunk = chunk.replace("</div>", "</div>\n" + toc, 1)  # after day-head
    day_stories = [m for m in STORIES if int(m["diary"]) == d["n"] or d["n"] in [int(x) for x in m["diary_also"]]]
    stories_box = ('<aside class="diary-link"><p>Stories Behind the Stones</p><ul>' + "".join(
        f'<li><a href="{m["url"]}">{html.escape(m["title"])}</a></li>' for m in day_stories) + '</ul></aside>\n') if day_stories else ""
    hero_fig = (f'<figure class="chapter-hero wide"><img src="/images/rajasthan/{d["img"]}.jpg" width="{d["w"]}" height="{d["h"]}" '
                f'alt="{d["alt"]}" fetchpriority="high">' + (f'<figcaption>{d["cap"]}</figcaption>' if d["cap"] else "") + '</figure>\n')
    body = (f'<article class="day-article">\n<div class="prose">{cr}<p class="series">Part of <a href="{COLL}">My Rajasthan Diaries</a> · Day {d["n"]} of 11</p></div>\n'
            + hero_fig + chunk +
            f'\n<div class="prose after-day">{stories_box}{share(d["url"], "Day " + str(d["n"]) + " — " + d["title"] + " | My Rajasthan Diaries")}{pager}'
            f'<p class="aside">Read <a href="{COMPLETE}#day-{d["n"]}">the complete travelogue</a> or '
            f'<a href="{COLL}">see all eleven days</a>.</p></div>\n</article>\n')
    title = f'Day {d["n"]} — {d["title"]} | My Rajasthan Diaries'
    desc = f'{strip_tags(d["sub"])} Day {d["n"]} of my eleven-day Rajasthan journey, {strip_tags(d["date"]).split(", ",1)[-1]} 2026.'
    img_url = f'{SITE}/images/rajasthan/{d["img"]}.jpg'
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": f'Day {d["n"]} — {d["title"]}', "alternativeHeadline": html.unescape(strip_tags(d["h2"])),
          "description": html.unescape(desc), "image": img_url, "datePublished": PUBLISHED, "dateModified": TODAY,
          "author": AUTHOR, "publisher": {"@type": "Organization", "name": "Miles & Memories", "url": SITE},
          "mainEntityOfPage": SITE + d["url"], "isPartOf": {"@type": "CreativeWorkSeries", "name": "My Rajasthan Diaries", "url": SITE + COLL},
          "inLanguage": "en"}
    page(d["url"], title=title, desc=html.escape(html.unescape(desc), quote=True), body=body, active="/travel-diaries/",
         og_type="article", og_image=(img_url, d["w"], d["h"], d["alt"]), jsonld=[ld, cr_ld], lightbox=True)

# ---------------------------------------------------------------- route map (drawn from approximate town coordinates)
STOPS = [("Jaipur", 26.92, 75.79, "w", "1–2"), ("Mandawa", 28.05, 75.15, "e", "3"), ("Pushkar", 26.49, 74.55, "s", "3–4"),
         ("Bikaner", 28.02, 73.31, "n", "4"), ("Jaisalmer", 26.92, 70.91, "n", "5–6"), ("Khuri", 26.60, 70.71, "s", "6"),
         ("Jodhpur", 26.24, 73.02, "e", "7"), ("Ranakpur", 25.12, 73.47, "w", "8"), ("Kumbhalgarh", 25.15, 73.59, "e", "8"),
         ("Nathdwara", 24.93, 73.82, "e", "9"), ("Udaipur", 24.58, 73.71, "s", "9–11")]
def route_map():
    x0, x1, y0, y1, W, H = 70.2, 76.6, 24.2, 28.6, 640, 440
    px = lambda lon: round((lon - x0) / (x1 - x0) * W, 1)
    py = lambda lat: round((y1 - lat) / (y1 - y0) * H, 1)
    pts = " ".join(f"{px(lon)},{py(lat)}" for _, lat, lon, *_ in STOPS)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="map-t map-d" class="route-map">',
           '<title id="map-t">Map of our route through Rajasthan</title>',
           '<desc id="map-d">' + ", then ".join(n for n, *_ in STOPS) + '. Positions are approximate.</desc>',
           f'<polyline points="{pts}" fill="none" stroke="var(--ochre)" stroke-width="2.5" stroke-dasharray="2 6" stroke-linecap="round"/>']
    for name, lat, lon, side, days in STOPS:
        x, y = px(lon), py(lat)
        dx, dy, anchor = {"e": (10, 4, "start"), "w": (-10, 4, "end"), "n": (0, -12, "middle"), "s": (0, 20, "middle")}[side]
        out.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="var(--sindoor)" stroke="var(--limewash)" stroke-width="2"/>'
                   f'<text x="{x + dx}" y="{y + dy}" text-anchor="{anchor}">{name} <tspan class="d">· Day {days}</tspan></text>')
    out.append("</svg>")
    return ('<figure class="route-figure wide">' + "".join(out) +
            '<figcaption>Our route, drawn from approximate town locations. Not to scale for driving.</figcaption></figure>\n')
# Interactive road-trip map (Leaflet, self-hosted; OpenStreetMap tiles; road route from the OSRM demo server,
# requested in the visitor's browser and cached. If routing fails, stops are joined by dashed straight lines
# and the note says so, so straight lines are never presented as roads.)
TRIP = [("Jaipur", 26.9124, 75.7873, "Days 1–2", [1, 2]), ("Mandawa", 28.0552, 75.1484, "Day 3", [3]),
        ("Pushkar", 26.4878, 74.5546, "Days 3–4", [3, 4]), ("Bikaner", 28.0229, 73.3119, "Day 4", [4]),
        ("Jaisalmer", 26.9157, 70.9083, "Days 5–6", [5, 6]), ("Khuri Desert", 26.6045, 70.7120, "Day 6", [6]),
        ("Jodhpur", 26.2389, 73.0243, "Day 7", [7]), ("Ranakpur", 25.1162, 73.4727, "Day 8", [8]),
        ("Kumbhalgarh", 25.1528, 73.5870, "Day 8", [8]), ("Nathdwara", 24.9381, 73.8228, "Day 9", [9]),
        ("Eklingji Temple, Kailashpuri", 24.7472, 73.7233, "Day 9", [9]), ("Udaipur", 24.5854, 73.7125, "Days 9–11", [9, 10, 11])]
def trip_map():
    stops = [{"name": n, "lat": la, "lng": lo, "days": dl,
              "links": [{"t": f"Day {k} — {DAYS[k-1]['title']}", "u": DAYS[k-1]["url"]} for k in ks]} for n, la, lo, dl, ks in TRIP]
    items = "".join(f'<li><span class="num">{i+1}</span> {n} <span class="d">· {dl}</span></li>' for i, (n, la, lo, dl, ks) in enumerate(TRIP))
    return f"""<section class="trip" aria-labelledby="trip-h">
  <h2 id="trip-h">My Rajasthan Diaries — 11-Day Road Trip</h2>
  <p class="when">10–20 October 2026</p>
  <div id="trip-map" role="region" aria-label="Interactive map of our route through Rajasthan"></div>
  <p class="trip-note" id="trip-note">Route shown for illustration; actual driving roads may vary.</p>
  <ol class="trip-stops">{items}</ol>
</section>
<link rel="stylesheet" href="/vendor/leaflet-1.9.4/leaflet.css">
<script src="/vendor/leaflet-1.9.4/leaflet.js"></script>
<script>
(() => {{
  const stops = {json.dumps(stops, ensure_ascii=False)};
  const css = getComputedStyle(document.documentElement);
  const navy = css.getPropertyValue('--indigo').trim() || '#1e2552';
  const mustard = css.getPropertyValue('--ochre').trim() || '#c98a12';
  const terracotta = css.getPropertyValue('--sindoor').trim() || '#a8232b';
  const map = L.map('trip-map', {{ scrollWheelZoom: false, zoomControl: true }});
  L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }}).addTo(map);
  const pts = stops.map(s => [s.lat, s.lng]);
  map.fitBounds(pts, {{ padding: [28, 28] }});
  stops.forEach((s, i) => {{
    const icon = L.divIcon({{ className: 'trip-pin', html: '<span>' + (i + 1) + '</span>', iconSize: [28, 28], iconAnchor: [14, 14], popupAnchor: [0, -12] }});
    const links = s.links.map(l => '<a href="' + l.u + '">' + l.t + '</a>').join('<br>');
    L.marker([s.lat, s.lng], {{ icon, title: s.name, keyboard: true }}).addTo(map)
      .bindPopup('<strong>' + (i + 1) + '. ' + s.name + '</strong><br><em>' + s.days + '</em><br>' + links);
  }});
  const draw = coords => {{
    L.polyline(coords, {{ color: navy, weight: 7, opacity: 0.35 }}).addTo(map);
    L.polyline(coords, {{ color: terracotta, weight: 3.5, opacity: 0.95 }}).addTo(map);
  }};
  const fallback = () => {{
    L.polyline(pts, {{ color: mustard, weight: 3, dashArray: '4 8', opacity: 0.9 }}).addTo(map);
    document.getElementById('trip-note').textContent = 'The road route could not be loaded just now, so dashed lines simply connect the stops in order. They are not roads.';
  }};
  const key = 'mm-rajasthan-route-v1';
  let cached = null;
  try {{ cached = JSON.parse(localStorage.getItem(key)); }} catch (e) {{}}
  if (cached) return draw(cached);
  const url = 'https://router.project-osrm.org/route/v1/driving/' + stops.map(s => s.lng + ',' + s.lat).join(';') + '?overview=full&geometries=geojson';
  fetch(url).then(r => r.ok ? r.json() : Promise.reject()).then(j => {{
    if (!j.routes || !j.routes.length) throw 0;
    const coords = j.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
    draw(coords);
    try {{ localStorage.setItem(key, JSON.stringify(coords)); }} catch (e) {{}}
  }}).catch(fallback);
}})();
</script>
"""

GALLERY = re.search(r'<section class="gallery" id="photos">.*?</section>', ARTICLE, re.S).group(0)

# ---------------------------------------------------------------- Rajasthan collection
cr, cr_ld = crumbs([("/", "Home"), ("/travel-diaries/", "Travel Diaries"), (None, "Rajasthan")])
hero = HERO.replace('<p class="dek">', cr + '    <p class="dek">', 1)
coll_body = (hero + "\n" + trip_map() + INTRO +
             f'\n<section class="stories">\n<h2>The diary, day by day</h2>\n' + "".join(day_card(d) for d in DAYS) +
             f'</section>\n<div class="prose more-links"><p><a class="button" href="{COMPLETE}">Read the complete travelogue →</a></p>'
             f'<p class="aside">Practical details from this trip are in <a href="/travel-notes/rajasthan-practical-notes/">Rajasthan: practical notes from our eleven days</a>.</p></div>\n'
             + GALLERY + '\n<div class="prose">' + share(COLL, "My Rajasthan Diaries | Miles & Memories") + '</div>\n')
coll_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "My Rajasthan Diaries",
           "url": SITE + COLL, "author": AUTHOR,
           "hasPart": [{"@type": "BlogPosting", "headline": f'Day {d["n"]} — {d["title"]}', "url": SITE + d["url"]} for d in DAYS]}
page(COLL, title="My Rajasthan Diaries: eleven days, day by day | Miles &amp; Memories",
     desc="An eleven-day Rajasthan journey through Jaipur, Mandawa, Pushkar, Bikaner, Jaisalmer, Jodhpur, Ranakpur, Kumbhalgarh and Udaipur, told day by day.",
     body=coll_body, active="/travel-diaries/", jsonld=[coll_ld, cr_ld], lightbox=True)

# ---------------------------------------------------------------- Travel Diaries archive
cr, cr_ld = crumbs([("/", "Home"), (None, "Travel Diaries")])
arch_body = (f'<header class="page-head">\n{cr}<h1>Travel Diaries</h1>\n'
             f'<p class="dek">Personal stories from cities, villages, historical sites and unexpected stops along the way.</p>\n</header>\n'
             f'<section class="stories">\n<h2>Destinations</h2>\n'
             f'<a class="story-card" href="{COLL}">\n  {thumb("r12", "Kalyani at the edge of Panna Meena ka Kund stepwell near Jaipur")}\n  <div>\n'
             f'    <p class="when">October 2026 · 11 days</p>\n    <h3>Rajasthan</h3>\n'
             f'    <p>Eleven days through royal cities, painted havelis, magnificent forts, ancient temples and the golden sands of Rajasthan.</p>\n'
             f'    <span class="read">Read My Rajasthan Diaries →</span>\n  </div>\n</a>\n</section>\n')
page("/travel-diaries/", title="Travel Diaries | Miles &amp; Memories",
     desc="Destination-by-destination travel diaries: personal stories from cities, villages, historical sites and unexpected stops, starting with Rajasthan.",
     body=arch_body, active="/travel-diaries/",
     jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Travel Diaries", "url": SITE + "/travel-diaries/"}, cr_ld])

# ---------------------------------------------------------------- category pages
# Intros reuse the wording already on the homepage cards. Day lists are tags chosen from the diary text.
# Travel guides
GUIDE = "/travel-notes/rajasthan-practical-notes/"
cr, cr_ld = crumbs([("/", "Home"), (None, "Travel Notes")])
guides_body = (f'<header class="page-head">\n{cr}<h1>Travel Notes</h1>\n'
               f'<p class="dek">Itineraries, accommodation, expenses, practical suggestions and what I’d do differently next time.</p>\n</header>\n'
               f'<section class="stories">\n<h2>Notes</h2>\n<a class="story-card" href="{GUIDE}">\n  {thumb("r14", "A red sandstone courtyard at Junagarh")}\n  <div>\n'
               f'    <p class="when">Rajasthan · October 2026</p>\n    <h3>Rajasthan: practical notes from our eleven days</h3>\n'
               f'    <p>Route and timing, costs and transport, the places we stayed, and advice for fellow art lovers.</p>\n'
               f'    <span class="read">Read the notes →</span>\n  </div>\n</a>\n</section>\n')
page("/travel-notes/", title="Travel Notes | Miles &amp; Memories",
     desc="Practical travel notes from my own journeys: itineraries, accommodation, costs and suggestions, starting with Rajasthan.",
     body=guides_body, active="/travel-notes/",
     jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Travel Notes", "url": SITE + "/travel-notes/"}, cr_ld])

cr, cr_ld = crumbs([("/", "Home"), ("/travel-notes/", "Travel Notes"), (None, "Rajasthan practical notes")])
notes = NOTES.replace('id="notes"', 'id="notes-guide"').replace("<h2>Notes for fellow travellers</h2>", "<h1>Rajasthan: practical notes from our eleven days</h1>", 1)
guide_body = (f'<article>\n<div class="prose page-top">{cr}</div>\n' + notes +
              f'\n<div class="prose">{DISCLAIMER}</div>\n' + ROUTE + "\n" + GLOSSARY +
              f'\n<div class="prose more-links"><p>The full story of this trip is in <a href="{COLL}">My Rajasthan Diaries</a>.</p></div>\n</article>\n')
page(GUIDE, title="Rajasthan: practical notes from an eleven-day trip | Miles &amp; Memories",
     desc="Route, timing, costs, transport and the places we stayed on an eleven-day Rajasthan trip in October 2026, with honest notes for fellow art lovers.",
     body=guide_body, active="/travel-notes/", og_type="article",
     jsonld=[{"@context": "https://schema.org", "@type": "Article", "headline": "Rajasthan: practical notes from our eleven days",
              "author": AUTHOR, "datePublished": PUBLISHED, "dateModified": TODAY, "image": SITE + "/images/og-rajasthan.jpg",
              "mainEntityOfPage": SITE + GUIDE}, cr_ld])

# ---------------------------------------------------------------- About / Contact
WELCOME = re.search(r'<section class="welcome" id="about">.*?</section>', HOME, re.S).group(0)
WELCOME_PARAS = re.findall(r"<p>.*?</p>", WELCOME)
cr, cr_ld = crumbs([("/", "Home"), (None, "About")])
BEYOND = re.search(r'<section class="beyond">.*?</section>', HOME, re.S).group(0)
CLOSING = re.search(r'<section class="closing">.*?</section>', HOME, re.S).group(0)
about_body = (f'<div class="prose page-top">{cr}</div>\n' + WELCOME.replace('id="about"', 'id="about-me"')
              .replace('loading="lazy" ', "").replace("<h2>Hello, I’m Kalyani.</h2>", "<h1>Hello, I’m Kalyani.</h1>")
              + "\n" + BEYOND + "\n" + CLOSING)
page("/about/", title="About Kalyani | Miles &amp; Memories",
     desc="About Kalyani, the traveller and traditional Indian art enthusiast behind Miles & Memories, a personal journal of heritage, art and travel.",
     body=about_body, active="/about/",
     jsonld=[{"@context": "https://schema.org", "@type": "AboutPage", "url": SITE + "/about/", "mainEntity": AUTHOR}, cr_ld])

cr, cr_ld = crumbs([("/", "Home"), (None, "Contact")])
contact_body = (f'<header class="page-head">\n{cr}<h1>Contact</h1>\n'
                f'<p class="dek">Have a travel story to share, a heritage site to recommend, or a question about one of my journeys? I’d love to hear from you.</p>\n</header>\n'
                f'<section class="contact-options" aria-label="Ways to get in touch">'
                f'<a class="contact-card wa" href="{WHATSAPP}" target="_blank" rel="noopener">{ICONS["whatsapp"]}<span class="cc-t">Chat on WhatsApp</span><span class="cc-d">+91 99801 54461</span></a>'
                f'<a class="contact-card" href="{INSTAGRAM}" target="_blank" rel="me noopener">{ICONS["instagram"]}<span class="cc-t">Instagram</span><span class="cc-d">@kalyanidarimisetty</span></a>'
                f'<a class="contact-card" href="{FACEBOOK}" target="_blank" rel="me noopener">{ICONS["facebook"]}<span class="cc-t">Facebook</span><span class="cc-d">facebook.com/kalyani.darimisetty</span></a>'
                f'</section>\n')
page("/contact/", title="Contact | Miles &amp; Memories",
     desc="How to get in touch with Kalyani at Miles & Memories.", body=contact_body, active="/contact/",
     jsonld=[{"@context": "https://schema.org", "@type": "ContactPage", "url": SITE + "/contact/"}, cr_ld])

# ---------------------------------------------------------------- Home
def home_block(marker_start, marker_end):
    return HOME.split(marker_start, 1)[1].split(marker_end, 1)[0]
hero = re.search(r'<section class="home-hero">.*?</section>', HOME, re.S).group(0).replace('href="/rajasthan/"', f'href="{COLL}"')
hero = hero.replace('<a class="button" href="' + COLL + '">Explore my travel diaries →</a>', '<a class="button" href="/travel-diaries/">Explore my travel diaries →</a>')
featured = re.search(r'<section class="featured">.*?</section>', HOME, re.S).group(0).replace('href="/rajasthan/"', f'href="{COLL}"')
featured = featured.replace('loading="lazy" alt=""', 'loading="lazy" alt="Two travellers in a haveli courtyard painted with elephants, horses and floral borders"')
featured = featured.replace('<section class="featured">', '<section class="featured" aria-labelledby="featured-h">\n    <h2 class="section-label" id="featured-h">Featured journey</h2>', 1)
featured = featured.replace('<p class="when">Featured journey, October 2026</p>', '<p class="when">October 2026</p>')
explore = re.search(r'<section class="explore">.*?</section>', HOME, re.S).group(0)
for old, new in (('href="/rajasthan/#day-3"', 'href="/art-heritage/"'), ('href="/rajasthan/#day-9"', 'href="/temples-traditions/"'),
                 ('href="/rajasthan/"', 'href="/travel-diaries/"'), ('href="/rajasthan/#notes"', 'href="/travel-notes/"'),
                 ("<h2>What you’ll find here</h2>", "<h2>Explore the journal</h2>")):
    assert old in explore, old
    explore = explore.replace(old, new)
beyond = re.search(r'<section class="beyond">.*?</section>', HOME, re.S).group(0)
closing = re.search(r'<section class="closing">.*?</section>', HOME, re.S).group(0)
intro = (WELCOME.split('<div class="welcome-text">')[0] + '<div class="welcome-text">\n      <h2>Hello, I’m Kalyani.</h2>\n      '
         + "\n      ".join(WELCOME_PARAS[:2]) + '\n      <p><a href="/about/">More about me →</a></p>\n    </div>\n  </section>')
# Latest stories: every article sorted by publish date (newest first). All Rajasthan chapters share one
# publish date, so ties fall back to the latest day. New journeys with later dates will appear first automatically.
ARTICLES = [dict(d, published=PUBLISHED) for d in DAYS]
latest = sorted(ARTICLES, key=lambda a: (a["published"], a["n"]), reverse=True)[:3]
recent = ('<section class="stories recent" aria-labelledby="recent-h">\n<h2 id="recent-h">Latest stories</h2>\n'
          + "".join(day_card(a) for a in latest) +
          f'<p><a href="{COLL}">See all eleven days of My Rajasthan Diaries →</a></p>\n</section>\n')
home_body = "\n".join([hero, intro, featured, explore, recent])
page("/", title="Miles &amp; Memories | Heritage, art and culture travel journal",
     desc="Journeys through places, people and heritage. A personal travel journal by Kalyani: forts, frescoes, crafts, temples and the stories behind them.",
     body=home_body, active="/",
     jsonld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "Miles & Memories", "url": SITE + "/",
              "description": "Journeys through places, people and heritage.", "author": AUTHOR, "inLanguage": "en"}])

DRAFT_NOTE = ('<p class="draft-flag">Draft for review. This story has not yet been checked and approved for publication.</p>\n')

def esc(t): return html.escape(str(t), quote=True)
def tag_key(t): return re.sub(r"[^a-z0-9]+", "-", str(t).lower()).strip("-")

def story_card(m):
    img = thumb(m["hero"], esc(m.get("hero_alt", ""))) if m.get("hero") not in (None, "none") else '<div class="card-noimg" aria-hidden="true"></div>'
    tags = " ".join(f"d-{tag_key(t)}" for t in m.get("destinations", [])) + " " + \
           " ".join(f"f-{tag_key(t)}" for t in m.get("figures", [])) + " " + " ".join(f"s-{tag_key(t)}" for t in m.get("subjects", []))
    return (f'<a class="sbs-card" href="{m["url"]}" data-tags="{tags.strip()}">{img}<div>'
            f'<p class="when">{esc(" · ".join(m.get("destinations", [])))}</p><h3>{esc(m["title"])}</h3>'
            f'<p>{esc(m["dek"])}</p></div></a>\n')

def render_md(md_text, published=False):
    out = markdown.markdown(md_text, extensions=["extra", "toc"])
    out = out.replace(" ⟨added⟩", "" if published else ' <mark class="added">added by editor</mark>')
    return out

for m in STORIES:
    d = DAYS[int(m["diary"]) - 1]
    cr, cr_ld = crumbs([("/", "Home"), (STORIES_PATH, "Stories Behind the Stones"), (None, esc(m["title"]))])
    hero = ""
    if m.get("hero") not in (None, "none"):
        w, h = Image.open(os.path.join(ROOT, f'images/rajasthan/{m["hero"]}.jpg')).size
        hero = (f'<figure class="chapter-hero wide"><img src="/images/rajasthan/{m["hero"]}.jpg" width="{w}" height="{h}" '
                f'alt="{esc(m.get("hero_alt", ""))}" fetchpriority="high"></figure>\n')
    gallery = ""
    pics = [x for x in m["photos"] if x and x != m.get("hero")]
    if pics:
        gallery = ('<figure class="day-photos"><div class="strip">' + "".join(
            f'<button data-full="{x}" aria-label="View larger"><img src="/images/rajasthan/{x}-sm.jpg" alt="Photograph from my visit" loading="lazy"></button>'
            for x in pics) + '</div><figcaption>From my visit.</figcaption></figure>\n')
    tags = "".join(f'<li>{esc(t)}</li>' for t in m.get("destinations", []) + m.get("figures", []) + m.get("subjects", []))
    diary_links = [DAYS[int(x) - 1] for x in [m["diary"]] + list(m["diary_also"])]
    diary_box = ('<aside class="diary-link"><p>From my travel diary</p><ul>' + "".join(
        f'<li><a href="{x["url"]}">Day {x["n"]} — {x["title"]}</a></li>' for x in diary_links) + '</ul></aside>\n')
    related = [BY_SLUG[r] for r in m["related"] if r in BY_SLUG][:3]
    rel = ('<section class="stories related"><h2>Related stories</h2><div class="sbs-grid">' + "".join(story_card(r) for r in related) + '</div></section>\n') if related else ""
    body = (f'<article class="story-article">\n<header class="page-head">{cr}<p class="series">Stories Behind the Stones</p>'
            f'<h1>{esc(m["title"])}</h1><p class="dek">{esc(m["dek"])}</p><ul class="tags">{tags}</ul></header>\n'
            + hero + '<div class="prose story-body">' + (DRAFT_NOTE if m.get("status") != "published" else "")
            + render_md(m["body_md"], m.get("status") == "published") + diary_box + share(m["url"], m["title"] + " | Stories Behind the Stones") + '</div>\n'
            + gallery + rel + '</article>\n')
    page(m["url"], title=f'{esc(m["title"])} | Stories Behind the Stones', desc=esc(m["dek"]), body=body,
         active=STORIES_PATH, og_type="article", noindex=m.get("status") != "published", lightbox=bool(pics),
         jsonld=[{"@context": "https://schema.org", "@type": "Article", "headline": m["title"], "description": m["dek"],
                  "author": AUTHOR, "about": m.get("figures", []) + m.get("destinations", []), "mainEntityOfPage": SITE + m["url"]}, cr_ld])

if STORIES:
    def chips(label, prefix, key):
        vals = sorted({t for m in STORIES for t in (m.get(key, []) if key == "subjects" else m.get(key, [])[:2])})  # main tags only, to keep the row short
        return (f'<div class="chip-row"><span>{label}</span>' + "".join(
            f'<button type="button" data-f="{prefix}-{tag_key(v)}">{esc(v)}</button>' for v in vals) + '</div>')
    cr, cr_ld = crumbs([("/", "Home"), (None, "Stories Behind the Stones")])
    sbs_body = (f'<header class="page-head sbs-head">\n{cr}<h1>Stories Behind the Stones</h1>\n'
                f'<p class="dek">History, legends and timeless wisdom from the places I’ve visited.</p>\n</header>\n'
                f'<div class="prose"><p>My travel diaries tell what I saw and felt. These stories go further back: the real history of the places, '
                f'the people connected with them, the legends told about them, and what they might still teach us. '
                f'Every story links back to the diary chapter where I visited the place.</p>'
                + (DRAFT_NOTE if any(m.get("status") != "published" for m in STORIES) else "") + '</div>\n'
                f'<section class="sbs-filter" aria-label="Browse stories"><p>Browse by</p>'
                + chips("Destination", "d", "destinations") + chips("Historical figure", "f", "figures") + chips("Subject", "s", "subjects")
                + '<button type="button" class="chip-clear" hidden>Show all stories</button></section>\n'
                f'<section class="stories sbs-list"><h2>Rajasthan</h2><div class="sbs-grid">' + "".join(story_card(m) for m in STORIES) + '</div></section>\n'
                + """<script>
(() => {
  const btns = document.querySelectorAll('.chip-row button'), clear = document.querySelector('.chip-clear');
  const cards = document.querySelectorAll('.sbs-list .sbs-card');
  const show = f => { cards.forEach(c => c.hidden = f && !c.dataset.tags.split(' ').includes(f));
    btns.forEach(b => b.setAttribute('aria-pressed', b.dataset.f === f)); clear.hidden = !f; };
  btns.forEach(b => b.addEventListener('click', () => show(b.getAttribute('aria-pressed') === 'true' ? null : b.dataset.f)));
  clear.addEventListener('click', () => show(null));
})();
</script>
""")
    page(STORIES_PATH, title="Stories Behind the Stones | Miles &amp; Memories",
         desc="History, legends and timeless wisdom from the places I’ve visited: the founders, rulers, artisans and traditions behind Rajasthan’s forts, temples and havelis.",
         body=sbs_body, active=STORIES_PATH, noindex=any(m.get("status") != "published" for m in STORIES),
         jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Stories Behind the Stones", "url": SITE + STORIES_PATH}, cr_ld])

# ---------------------------------------------------------------- category pages
# Each category gathers (1) Stories Behind the Stones on its subjects and (2) the specific diary sections on its theme,
# linked to their place in the chapter. Section choices are from the diary's own sub-headings.
CATS = {
    "/art-heritage/": dict(name="Art &amp; Heritage",
        intro="Traditional paintings, local crafts, museums, architecture and the artists who keep these traditions alive.",
        desc="Art and heritage from my travels: painted havelis, palace interiors, forts, stepwells and carved stone.",
        story_subjects={"Art & Craft", "Forts & Palaces", "Merchants & Trade", "Science & Astronomy"}, exclude_subjects={"Temples & Faith"},
        sections=[(2, "Amer: grandeur in layers"), (2, "Panna Meena ka Kund: a memory from childhood"), (3, "Why Shekhawati is a painted world"),
                  (4, "Junagarh: the palace of details"), (4, "The Rampuria Havelis"),
                  (6, "A fort that is also a neighbourhood"), (7, "The fort above the city"), (10, "City Palace and a change of hotel")]),
    "/temples-traditions/": dict(name="Temples &amp; Traditions",
        intro="Sacred places, their histories, fascinating legends and the experiences that make each visit special.",
        desc="Temples and traditions from my travels: Pushkar's Brahma Temple, Ranakpur Jain Temple, Shrinathji at Nathdwara and Eklingji.",
        story_subjects={"Temples & Faith"}, exclude_subjects=set(),
        sections=[(4, None), (8, "Ranakpur: marble that seems almost weightless"), (9, "Shrinathji and Eklingji")]),
}
SECTION_LABELS = {(4, None): "Pushkar: the Brahma Temple and the lake ghats"}
# Photo for each section card, chosen by hand so it shows that place (None = no photo of it).
SECTION_PHOTOS = {(2, "Amer: grandeur in layers"): "jp22", (2, "Panna Meena ka Kund: a memory from childhood"): "jp21",
    (3, "Why Shekhawati is a painted world"): "r06", (3, "The haveli I wanted to take home"): "r04",
    (4, "Junagarh: the palace of details"): "jg09", (4, "The Rampuria Havelis"): "b02",
    (6, "A fort that is also a neighbourhood"): "js03", (7, "The fort above the city"): "j08",
    (10, "City Palace and a change of hotel"): "cp02", (10, "Shilpgram: buying from the people who make it"): "s02",
    (4, None): "p02", (8, "Ranakpur: marble that seems almost weightless"): "n02",
    (9, "A full evening in the old city"): "ue01", (6, "Khuri: the desert after dark"): "k04", (5, "Bada Bagh at six"): "bb02"}

def h3_anchor(t): return re.sub(r"[^a-z0-9]+", "-", strip_tags(t).lower()).strip("-")

def section_card(n, h3):
    d = DAYS[n - 1]; chunk = d["chunk"]
    if h3:
        assert f"<h3>{h3}</h3>" in chunk, h3
        after = chunk.split(f"<h3>{h3}</h3>", 1)[1]
        url = d["url"] + "#" + h3_anchor(h3); label = h3
        first_p = re.search(r"<p>(.*?)</p>", after, re.S).group(1)
    else:
        after = chunk; url = d["url"]; label = SECTION_LABELS[(n, h3)]
        first_p = re.search(r"<p>(.*?)</p>", chunk, re.S).group(1)
    pid = SECTION_PHOTOS.get((n, h3))
    if pid:
        alt = re.search(r'data-full="%s" aria-label="View larger: ([^"]*)"' % pid, SRC) or re.search(r'/images/rajasthan/%s(?:-sm)?\.jpg"[^>]*alt="([^"]*)"' % pid, SRC)
        img = thumb(pid, alt.group(1))
    else:
        img = '<div class="card-noimg" aria-hidden="true"></div>' 
    excerpt = strip_tags(first_p); excerpt = excerpt if len(excerpt) < 170 else excerpt[:excerpt.rfind(" ", 0, 165)] + "…"
    return (f'<a class="sbs-card" href="{url}">{img}<div><p class="when">Day {n} — {d["title"]}</p>'
            f'<h3>{label}</h3><p>{html.escape(excerpt)}</p></div></a>\n')

for path, c in CATS.items():
    cr, cr_ld = crumbs([("/", "Home"), (None, c["name"])])
    sts = [m for m in STORIES if set(m.get("subjects", [])) & c["story_subjects"] and not set(m.get("subjects", [])) & c["exclude_subjects"]]
    body = f'<header class="page-head">\n{cr}<h1>{c["name"]}</h1>\n<p class="dek">{c["intro"]}</p>\n</header>\n'
    body += ('<section class="stories cat-block"><h2>From my travel diaries</h2><div class="sbs-grid">'
             + "".join(section_card(n, h) for n, h in c["sections"]) + "</div></section>\n")
    if sts and c.get("show_stories"):  # stories live in their own section; off by default
        body += ('<section class="stories cat-block"><h2>Stories Behind the Stones</h2><div class="sbs-grid">'
                 + "".join(story_card(m) for m in sts) + f'</div><p><a href="{STORIES_PATH}">All Stories Behind the Stones →</a></p></section>\n')
    page(path, title=f'{c["name"]} | Miles &amp; Memories', desc=c["desc"], body=body, active=path,
         jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": strip_tags(c["name"]), "url": SITE + path}, cr_ld])

# ---------------------------------------------------------------- sitemap
urls = ["/", "/travel-diaries/", COLL] + [d["url"] for d in DAYS] + ["/art-heritage/", "/temples-traditions/",
        "/travel-notes/", GUIDE, "/about/", "/contact/"]
urls += ([STORIES_PATH] if STORIES and all(m.get("status") == "published" for m in STORIES) else []) + [m["url"] for m in STORIES if m.get("status") == "published"]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
write("search-index.json", json.dumps(sorted(SEARCH_INDEX, key=lambda p: p["u"]), ensure_ascii=False))
print("built", len(urls) + 1, "pages")
