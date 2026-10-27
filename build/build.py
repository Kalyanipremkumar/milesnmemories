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

# ---------------------------------------------------------------- navigation
NAV = [("/", "Home"), ("/travel-diaries/", "Travel Diaries"), ("/art-heritage/", "Art &amp; Heritage"),
       ("/temples-traditions/", "Temples &amp; Traditions"), ("/travel-guides/", "Travel Guides"),
       ("/about/", "About"), ("/contact/", "Contact")]

def header(active):
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{u}"{cur if u == active else ""}>{t}</a>' for u, t in NAV)
    return (f'<header class="site-head">\n  <a class="wordmark" href="/">Miles &amp; Memories</a>\n'
            f'  <nav aria-label="Main">{links}</nav>\n</header>\n')

FOOTER = """<footer class="site-foot">
  <span>© 2026 Miles &amp; Memories</span>
  <span class="foot-links"><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/travel-diaries/">Travel Diaries</a></span>
  <span class="social"><a href="https://www.instagram.com/kalyanidarimisetty/" rel="me noopener" target="_blank">Instagram</a><a href="https://www.facebook.com/kalyani.darimisetty/" rel="me noopener" target="_blank">Facebook</a></span>
  <span>milesnmemories.travel</span>
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=Rozha+One&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
</head>
<body>
"""
    head = re.sub(r"\n\n+", "\n", head)
    out = (head + header(active) + "\n<main>\n" + (DISCLOSURE if disclosure else "") + body + "\n</main>\n\n"
           + (LIGHTBOX if lightbox else "") + "\n" + FOOTER + "</body>\n</html>\n")
    out = pictures(out)
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

SLUGS = ["day-1-jaipur-pink-city", "day-2-jaipur-forts-stepwell", "day-3-mandawa-painted-havelis",
         "day-4-pushkar-bikaner", "day-5-jaisalmer-bada-bagh", "day-6-jaisalmer-khuri",
         "day-7-jodhpur-rohet-garh", "day-8-ranakpur-kumbhalgarh", "day-9-nathdwara-udaipur",
         "day-10-udaipur-art-markets", "day-11-journey-home"]
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
    DAYS.append(dict(n=i + 1, slug=SLUGS[i], url=COLL + SLUGS[i] + "/", chunk=chunk, date=date_, h2=h2,
                     sub=sub, img=img_id, alt=alt_m.group(1), w=w, h=h))

def day_card(d, heading="h3"):
    return (f'<a class="story-card" href="{d["url"]}">\n  {thumb(d["img"], d["alt"])}\n  <div>\n'
            f'    <p class="when">{d["date"]}</p>\n    <{heading}>{d["h2"]}</{heading}>\n'
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

# ---------------------------------------------------------------- complete travelogue
complete_body = "<article>" + ARTICLE + "</article>\n"
complete_body = complete_body.replace(
    '<p class="dek">', f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">/</span> '
    f'<a href="/travel-diaries/">Travel Diaries</a> <span aria-hidden="true">/</span> <a href="{COLL}">Rajasthan</a></nav>\n    <p class="dek">', 1)
complete_body = complete_body.replace(
    '<nav class="toc" aria-label="Days">',
    f'<p class="prose aside">Prefer one day at a time? <a href="{COLL}">Read the diary day by day</a>.</p>\n  <nav class="toc" aria-label="Days">', 1)
page(COMPLETE, title="My Rajasthan Diaries: the complete travelogue | Miles &amp; Memories",
     desc="All eleven days of my October 2026 Rajasthan journey on one page: forts, frescoes, temples, desert skies and stories.",
     body=complete_body, active="/travel-diaries/", noindex=True, og_type="article", lightbox=True)

# ---------------------------------------------------------------- day articles
for i, d in enumerate(DAYS):
    prev_ = DAYS[i - 1] if i else None
    next_ = DAYS[i + 1] if i < 10 else None
    cr, cr_ld = crumbs([("/", "Home"), ("/travel-diaries/", "Travel Diaries"), (COLL, "Rajasthan"), (None, f"Day {d['n']}")])
    pager = '<nav class="pager" aria-label="More days">'
    pager += (f'<a class="prev" href="{prev_["url"]}"><span>← Day {prev_["n"]}</span>{prev_["h2"]}</a>' if prev_ else '<span></span>')
    pager += (f'<a class="next" href="{next_["url"]}"><span>Day {next_["n"]} →</span>{next_["h2"]}</a>' if next_ else '<span></span>')
    pager += "</nav>\n"
    chunk = d["chunk"]
    # the day heading becomes the page's h1; everything else stays exactly as written
    chunk = chunk.replace(f"<h2>{d['h2']}</h2>", f"<h1>{d['h2']}</h1>", 1)
    body = (f'<article class="day-article">\n<div class="prose">{cr}<p class="series">Part of <a href="{COLL}">My Rajasthan Diaries</a> · Day {d["n"]} of 11</p></div>\n'
            + chunk +
            f'\n<div class="prose after-day">{pager}<p class="aside">Read <a href="{COMPLETE}#day-{d["n"]}">the complete travelogue</a> or '
            f'<a href="{COLL}">see all eleven days</a>.</p></div>\n</article>\n')
    title = f'Day {d["n"]}: {strip_tags(d["h2"])} | Rajasthan Diaries'
    desc = f'{strip_tags(d["sub"])} Day {d["n"]} of my eleven-day Rajasthan journey, {strip_tags(d["date"]).split(", ",1)[-1]} 2026.'
    img_url = f'{SITE}/images/rajasthan/{d["img"]}.jpg'
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": html.unescape(strip_tags(d["h2"])),
          "description": html.unescape(desc), "image": img_url, "datePublished": PUBLISHED, "dateModified": TODAY,
          "author": AUTHOR, "publisher": {"@type": "Organization", "name": "Miles & Memories", "url": SITE},
          "mainEntityOfPage": SITE + d["url"], "isPartOf": {"@type": "CreativeWorkSeries", "name": "My Rajasthan Diaries", "url": SITE + COLL},
          "inLanguage": "en"}
    page(d["url"], title=title, desc=html.escape(html.unescape(desc), quote=True), body=body, active="/travel-diaries/",
         og_type="article", og_image=(img_url, d["w"], d["h"], d["alt"]), jsonld=[ld, cr_ld], lightbox=True)

# ---------------------------------------------------------------- Rajasthan collection
cr, cr_ld = crumbs([("/", "Home"), ("/travel-diaries/", "Travel Diaries"), (None, "Rajasthan")])
hero = HERO.replace('<p class="dek">', cr + '    <p class="dek">', 1)
coll_body = (hero + "\n" + ROUTE + "\n" + INTRO +
             f'\n<section class="stories">\n<h2>The diary, day by day</h2>\n' + "".join(day_card(d) for d in DAYS) +
             f'</section>\n<div class="prose more-links"><p><a class="button" href="{COMPLETE}">Read the complete travelogue →</a></p>'
             f'<p class="aside">Practical details from this trip are in <a href="/travel-guides/rajasthan-practical-notes/">Rajasthan: practical notes from our eleven days</a>.</p></div>\n')
coll_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "My Rajasthan Diaries",
           "url": SITE + COLL, "author": AUTHOR,
           "hasPart": [{"@type": "BlogPosting", "headline": html.unescape(strip_tags(d["h2"])), "url": SITE + d["url"]} for d in DAYS]}
page(COLL, title="My Rajasthan Diaries: eleven days, day by day | Miles &amp; Memories",
     desc="An eleven-day Rajasthan journey through Jaipur, Mandawa, Pushkar, Bikaner, Jaisalmer, Jodhpur, Ranakpur, Kumbhalgarh and Udaipur, told day by day.",
     body=coll_body, active="/travel-diaries/", jsonld=[coll_ld, cr_ld])

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
CATS = {
    "/art-heritage/": ("Art &amp; Heritage", "Traditional paintings, local crafts, museums, architecture and the artists who keep these traditions alive.",
                       [1, 2, 3, 4, 6, 7, 10], "Art and heritage stories: frescoes, carved havelis, palace interiors, crafts and the artists behind them, from my Rajasthan travel diaries."),
    "/temples-traditions/": ("Temples &amp; Traditions", "Sacred places, their histories, fascinating legends and the experiences that make each visit special.",
                             [4, 8, 9], "Temples and traditions from my travels: Pushkar's Brahma Temple, Ranakpur, Shrinathji, Eklingji, Jagdish Temple and folk performance in Udaipur."),
}
for path, (name, intro, days, desc) in CATS.items():
    cr, cr_ld = crumbs([("/", "Home"), (None, name)])
    body = (f'<header class="page-head">\n{cr}<h1>{name}</h1>\n<p class="dek">{intro}</p>\n</header>\n'
            f'<section class="stories">\n<h2>From the Rajasthan diaries</h2>\n'
            + "".join(day_card(DAYS[n - 1]) for n in days) + "</section>\n")
    page(path, title=f"{name} | Miles &amp; Memories", desc=desc, body=body, active=path,
         jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": strip_tags(name), "url": SITE + path,
                  "hasPart": [{"@type": "BlogPosting", "headline": html.unescape(strip_tags(DAYS[n-1]["h2"])), "url": SITE + DAYS[n-1]["url"]} for n in days]}, cr_ld])

# Travel guides
GUIDE = "/travel-guides/rajasthan-practical-notes/"
cr, cr_ld = crumbs([("/", "Home"), (None, "Travel Guides")])
guides_body = (f'<header class="page-head">\n{cr}<h1>Travel Guides</h1>\n'
               f'<p class="dek">Itineraries, accommodation, expenses, practical suggestions and what I’d do differently next time.</p>\n</header>\n'
               f'<section class="stories">\n<h2>Guides</h2>\n<a class="story-card" href="{GUIDE}">\n  {thumb("r14", "A red sandstone courtyard at Junagarh")}\n  <div>\n'
               f'    <p class="when">Rajasthan · October 2026</p>\n    <h3>Rajasthan: practical notes from our eleven days</h3>\n'
               f'    <p>Route and timing, costs and transport, the places we stayed, and advice for fellow art lovers.</p>\n'
               f'    <span class="read">Read the guide →</span>\n  </div>\n</a>\n</section>\n')
page("/travel-guides/", title="Travel Guides | Miles &amp; Memories",
     desc="Practical travel guides from my own journeys: itineraries, accommodation, costs and suggestions, starting with Rajasthan.",
     body=guides_body, active="/travel-guides/",
     jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Travel Guides", "url": SITE + "/travel-guides/"}, cr_ld])

cr, cr_ld = crumbs([("/", "Home"), ("/travel-guides/", "Travel Guides"), (None, "Rajasthan practical notes")])
notes = NOTES.replace('id="notes"', 'id="notes-guide"').replace("<h2>Notes for fellow travellers</h2>", "<h1>Rajasthan: practical notes from our eleven days</h1>", 1)
guide_body = (f'<article>\n<div class="prose page-top">{cr}</div>\n' + notes +
              f'\n<div class="prose">{DISCLAIMER}</div>\n' + ROUTE + "\n" + GLOSSARY +
              f'\n<div class="prose more-links"><p>The full story of this trip is in <a href="{COLL}">My Rajasthan Diaries</a>.</p></div>\n</article>\n')
page(GUIDE, title="Rajasthan: practical notes from an eleven-day trip | Miles &amp; Memories",
     desc="Route, timing, costs, transport and the places we stayed on an eleven-day Rajasthan trip in October 2026, with honest notes for fellow art lovers.",
     body=guide_body, active="/travel-guides/", og_type="article",
     jsonld=[{"@context": "https://schema.org", "@type": "Article", "headline": "Rajasthan: practical notes from our eleven days",
              "author": AUTHOR, "datePublished": PUBLISHED, "dateModified": TODAY, "image": SITE + "/images/og-rajasthan.jpg",
              "mainEntityOfPage": SITE + GUIDE}, cr_ld])

# ---------------------------------------------------------------- About / Contact
WELCOME = re.search(r'<section class="welcome" id="about">.*?</section>', HOME, re.S).group(0)
WELCOME_PARAS = re.findall(r"<p>.*?</p>", WELCOME)
cr, cr_ld = crumbs([("/", "Home"), (None, "About")])
about_body = (f'<div class="prose page-top">{cr}</div>\n' + WELCOME.replace('id="about"', 'id="about-me"')
              .replace('loading="lazy" ', "").replace("<h2>Hello, I’m Kalyani.</h2>", "<h1>Hello, I’m Kalyani.</h1>"))
page("/about/", title="About Kalyani | Miles &amp; Memories",
     desc="About Kalyani, the traveller and traditional Indian art enthusiast behind Miles & Memories, a personal journal of heritage, art and travel.",
     body=about_body, active="/about/",
     jsonld=[{"@context": "https://schema.org", "@type": "AboutPage", "url": SITE + "/about/", "mainEntity": AUTHOR}, cr_ld])

cr, cr_ld = crumbs([("/", "Home"), (None, "Contact")])
contact_body = (f'<header class="page-head">\n{cr}<h1>Contact</h1>\n'
                f'<p class="dek">The easiest way to reach me is through Instagram or Facebook.</p>\n</header>\n'
                f'<div class="prose contact-links"><p><a class="button" href="https://www.instagram.com/kalyanidarimisetty/" rel="me noopener" target="_blank">Instagram</a> '
                f'<a class="button" href="https://www.facebook.com/kalyani.darimisetty/" rel="me noopener" target="_blank">Facebook</a></p></div>\n')
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
featured = featured.replace('<section class="featured">', '<section class="featured" aria-labelledby="featured-h">\n    <h2 class="section-label" id="featured-h">Featured journeys</h2>', 1)
explore = re.search(r'<section class="explore">.*?</section>', HOME, re.S).group(0)
for old, new in (('href="/rajasthan/#day-3"', 'href="/art-heritage/"'), ('href="/rajasthan/#day-9"', 'href="/temples-traditions/"'),
                 ('href="/rajasthan/"', 'href="/travel-diaries/"'), ('href="/rajasthan/#notes"', 'href="/travel-guides/"'),
                 ("<h3>Travel Notes</h3>", "<h3>Travel Guides</h3>")):
    assert old in explore, old
    explore = explore.replace(old, new)
beyond = re.search(r'<section class="beyond">.*?</section>', HOME, re.S).group(0)
closing = re.search(r'<section class="closing">.*?</section>', HOME, re.S).group(0)
intro = (WELCOME.split('<div class="welcome-text">')[0] + '<div class="welcome-text">\n      <h2>Hello, I’m Kalyani.</h2>\n      '
         + "\n      ".join(WELCOME_PARAS[:2]) + '\n      <p><a href="/about/">More about me →</a></p>\n    </div>\n  </section>')
recent = ('<section class="stories recent" aria-labelledby="recent-h">\n<h2 id="recent-h">Recent articles</h2>\n'
          + "".join(day_card(DAYS[n - 1]) for n in (1, 2, 3)) +
          f'<p><a href="{COLL}">See all eleven days of My Rajasthan Diaries →</a></p>\n</section>\n')
home_body = "\n".join([hero, intro, featured, recent, explore, beyond, closing])
page("/", title="Miles &amp; Memories | Heritage, art and culture travel journal",
     desc="Journeys through places, people and heritage. A personal travel journal by Kalyani: forts, frescoes, crafts, temples and the stories behind them.",
     body=home_body, active="/",
     jsonld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "Miles & Memories", "url": SITE + "/",
              "description": "Journeys through places, people and heritage.", "author": AUTHOR, "inLanguage": "en"}])

# ---------------------------------------------------------------- sitemap
urls = ["/", "/travel-diaries/", COLL] + [d["url"] for d in DAYS] + ["/art-heritage/", "/temples-traditions/",
        "/travel-guides/", GUIDE, "/about/", "/contact/"]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
print("built", len(urls) + 1, "pages")
