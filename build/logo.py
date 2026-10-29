#!/usr/bin/env python3
"""Generates the Miles & Memories logo set as outlined SVG (no font dependency) plus transparent PNGs.

Typeface: Playfair Display (SIL Open Font License; see build/fonts/OFL-PlayfairDisplay.txt).
Run from the repo root:  python3 build/logo.py
"""
import io, os
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
import cairosvg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "build/fonts")
OUT = os.path.join(ROOT, "brand")
NAVY, GOLD, TERRA, IVORY = "#182B54", "#C38A24", "#A43B2D", "#F8F5EE"


class Face:
    def __init__(self, fn):
        tt = TTFont(os.path.join(FONTS, fn)); tt.flavor = None
        buf = io.BytesIO(); tt.save(buf); data = buf.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.hbfont = hb.Font(hb.Face(hb.Blob(data)))
        self.upm = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()

    def run(self, text, size, x, y, tracking=0.0):
        """Shape text with HarfBuzz (kerning, ligatures); return (path d, bbox, advance)."""
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {"kern": True, "liga": True})
        s = size / self.upm
        pen = SVGPathPen(self.gs); bp = BoundsPen(self.gs)
        cx = x
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.order[info.codepoint]
            t = (s, 0, 0, -s, cx + pos.x_offset * s, y - pos.y_offset * s)
            self.gs[name].draw(TransformPen(pen, t)); self.gs[name].draw(TransformPen(bp, t))
            cx += pos.x_advance * s + tracking * size
        adv = cx - x - tracking * size
        return pen.getCommands(), bp.bounds, adv


BOLD = Face("playfair-display-latin-700-normal.woff")
ITAL = Face("playfair-display-latin-400-italic.woff")
MED = Face("playfair-display-latin-500-normal.woff")


def lotus(cx, base_y, h, color=TERRA):
    """Three-petal lotus bud: a pan-Indian motif, not tied to any one region."""
    def petal(rot, scale):
        w, hh = 0.36 * h * scale, h * scale
        d = (f"M0 0 C{w:.2f} {-hh*0.28:.2f} {w*0.9:.2f} {-hh*0.72:.2f} 0 {-hh:.2f} "
             f"C{-w*0.9:.2f} {-hh*0.72:.2f} {-w:.2f} {-hh*0.28:.2f} 0 0Z")
        return f'<path transform="translate({cx:.2f} {base_y:.2f}) rotate({rot})" d="{d}"/>'
    return (f'<g fill="{color}">' + petal(-52, 0.78) + petal(52, 0.78) + petal(0, 1.0) + "</g>")


def union(*bbs):
    bbs = [b for b in bbs if b]
    return (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs))


def wordmark(size=100, y=0, x=0, amp_scale=1.18, lotus_on=True, ink=NAVY, lotus_color=TERRA):
    """'Miles & Memories' on one line. Returns svg fragment, bbox."""
    d1, b1, a1 = BOLD.run("Miles", size, x, y, 0.005)
    gap = size * 0.10
    amp_size = size * amp_scale
    ax = x + a1 + gap
    da, ba, aa = ITAL.run("&", amp_size, ax, y + size * 0.02)
    mx = ba[2] + gap
    d2, b2, a2 = BOLD.run("Memories", size, mx, y, 0.005)
    parts = [f'<path fill="{ink}" d="{d1}"/>', f'<path fill="{GOLD}" d="{da}"/>', f'<path fill="{ink}" d="{d2}"/>']
    bb = union(b1, ba, b2)
    if lotus_on:
        lh = size * 0.38
        lcx = (ba[0] + ba[2]) / 2 + size * 0.06
        base = ba[1] - size * 0.06
        parts.append(lotus(lcx, base, lh, lotus_color))
        bb = union(bb, (lcx - lh * 0.6, base - lh, lcx + lh * 0.6, base))
    return "".join(parts), bb


def tagline(cx, y, size, width):
    words = ["HERITAGE", "CULTURE", "JOURNEYS"]
    track = 0.32
    runs = [MED.run(w, size, 0, 0, track) for w in words]
    dia = size * 0.42; sep = size * 1.6
    total = sum(r[2] for r in runs) + 2 * (sep * 2 + dia)
    x = cx - total / 2
    parts = []; bb = None
    for i, w in enumerate(words):
        d, b, a = MED.run(w, size, x, y, track)
        parts.append(f'<path fill="{GOLD}" d="{d}"/>'); bb = union(bb, b) if bb else b
        x += a
        if i < 2:
            dx = x + sep + dia / 2; dy = y - size * 0.36
            parts.append(f'<path fill="{TERRA}" d="M{dx:.2f} {dy-dia/2:.2f}L{dx+dia/2:.2f} {dy:.2f}L{dx:.2f} {dy+dia/2:.2f}L{dx-dia/2:.2f} {dy:.2f}Z"/>')
            x += sep * 2 + dia
    # hairline rules either side
    left_end, right_start = cx - total / 2 - size * 1.2, cx + total / 2 + size * 1.2
    ry = y - size * 0.36
    half = width / 2
    parts.append(f'<path stroke="{GOLD}" stroke-width="{size*0.07:.2f}" stroke-linecap="round" d="M{cx-half:.2f} {ry:.2f}H{left_end:.2f}M{right_start:.2f} {ry:.2f}H{cx+half:.2f}"/>')
    return "".join(parts), union(bb, (cx - half, ry - 1, cx + half, ry + 1))


def svg(body, bb, pad, title, bg=None):
    x0, y0, x1, y1 = bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad
    w, h = x1 - x0, y1 - y0
    rect = f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{rect}{body}</svg>\n'), w, h


def save(name, content, png_widths=(), bg=None):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name + ".svg"), "w").write(content)
    for pw in png_widths:
        cairosvg.svg2png(bytestring=content.encode(), write_to=os.path.join(OUT, f"{name}-{pw}.png"), output_width=pw)


# 1. Primary logo: wordmark + tagline (header on desktop, documents, social)
wm, wbb = wordmark(100)
tg, tbb = tagline((wbb[0] + wbb[2]) / 2, wbb[3] + 46, 17, (wbb[2] - wbb[0]))
primary, pw_, ph_ = svg(wm + tg, union(wbb, tbb), 6, "Miles &amp; Memories — Heritage, Culture, Journeys")
save("logo-primary", primary, (600, 1200, 2400))

# 2. Compact logo: wordmark only, smaller lotus (mobile header, footers)
cm, cbb = wordmark(100, amp_scale=1.12)
compact, _, _ = svg(cm, cbb, 4, "Miles &amp; Memories")
save("logo-compact", compact, (400, 800))

# 2b. Reversed compact logo for dark (navy) backgrounds: ivory letters, gold ampersand and lotus
rm, rbb = wordmark(100, amp_scale=1.12, ink=IVORY, lotus_color=GOLD)
reversed_, _, _ = svg(rm, rbb, 4, "Miles &amp; Memories")
save("logo-compact-reversed", reversed_, (400, 800))

# 3. Monogram: M&M in a gold ring on ivory (favicon, avatars)
R = 100
m1, b1, a1 = BOLD.run("M", 74, 0, 0)
am, ba, aa = ITAL.run("&", 80, a1 - 6, 4)
m2, b2, a2 = BOLD.run("M", 74, ba[2] - 6, 0)
gb = union(b1, ba, b2)
gw, gh = gb[2] - gb[0], gb[3] - gb[1]
k = 134 / gw                                   # keep letters well inside the ring
tx, ty = -(gb[0] + gw / 2) * k, -(gb[1] + gh / 2) * k
mono_body = (f'<circle r="{R-4}" fill="{IVORY}" stroke="{GOLD}" stroke-width="6"/>'
             f'<g transform="translate({tx:.2f} {ty:.2f}) scale({k:.4f})"><path fill="{NAVY}" d="{m1}"/><path fill="{GOLD}" d="{am}"/><path fill="{NAVY}" d="{m2}"/></g>')
mono = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-R} {-R} {2*R} {2*R}" role="img" aria-label="Miles &amp; Memories">'
        f'<title>Miles &amp; Memories</title>{mono_body}</svg>\n')
save("monogram", mono, (32, 180, 512))

# 4. Favicon: the same M&M, reversed out of a navy disc and drawn larger, so it stays legible at 16-32 px
kf = 172 / gw
fx, fy = -(gb[0] + gw / 2) * kf, -(gb[1] + gh / 2) * kf
fav = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-R} {-R} {2*R} {2*R}"><title>Miles &amp; Memories</title>'
       f'<circle r="{R}" fill="{NAVY}"/><circle r="{R-9}" fill="none" stroke="{GOLD}" stroke-width="5"/>'
       f'<g transform="translate({fx:.2f} {fy:.2f}) scale({kf:.4f})"><path fill="{IVORY}" d="{m1}"/><path fill="{GOLD}" d="{am}"/><path fill="{IVORY}" d="{m2}"/></g></svg>\n')
save("favicon", fav, (16, 32, 48))
open(os.path.join(ROOT, "favicon.svg"), "w").write(fav)
cairosvg.svg2png(bytestring=fav.encode(), write_to=os.path.join(ROOT, "favicon-32.png"), output_width=32)
cairosvg.svg2png(bytestring=mono.encode(), write_to=os.path.join(ROOT, "apple-touch-icon.png"), output_width=180)
print("primary", round(pw_), "x", round(ph_), "| written to", OUT)
