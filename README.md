# curiousfish.org

A deliberately simple static site.

Edit these files directly:

- `index.html` — all page content, including the manually curated sections
- `style.css` — all styling

There is no build step. Open `index.html` in a browser, or run a tiny local server:

```sh
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Updating profile stats

The stats cards in `index.html` are the only automated part. Update them manually with:

```sh
python3 scripts/update_stats.py
```

GitHub Actions also runs the same script every two days and commits `index.html` if the numbers changed.

## Deploying

Deploy the current files as-is. `.assetsignore` keeps non-public files out of the upload, while `worker.js` only serves `/`, `/index.html`, `/style.css`, and `/images/*`.

```sh
wrangler deploy
```
