# Miles & Memories

Personal travel journal at milesnmemories.travel. Plain static HTML and CSS, deployed on Vercel.

- `index.html` — home page and story list
- `rajasthan/index.html` — My Rajasthan Diaries (October 2026)
- `styles.css` — shared styles
- `images/<trip>/` — photos (`rNN.jpg` full size, `rNN-sm.jpg` thumbnails)

To add a trip: copy `rajasthan/` to a new folder, replace the text and photos, and add a card to the Stories list in `index.html`. Every push to `main` deploys automatically.

## Site structure (October 2026)
- Rajasthan writing lives in **`src/rajasthan.html`**, the single source. Day articles, the complete travelogue, category pages and the guide are generated from it. Original homepage wording is in `src/home-original.html`.
- After editing either, run `python3 build/build.py` and commit the generated files.
- New photos: add `X.jpg` and `X-sm.jpg` to `images/rajasthan/`, plus WebP versions (`X.webp`, `X-960.webp`, `X-480.webp`, `X-sm.webp`).
- Future monetisation hooks (not active): `page(..., disclosure=True)` adds an affiliate disclosure; downloadable guides go under `/downloads/`; a shop page can be added with `page()` and a `NAV` entry. No ads.
