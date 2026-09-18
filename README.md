# curiousfish.org

A static homepage built from Markdown and served by a Cloudflare Worker.

## Edit

Edit `notable.md` for New & Notable. Items appear in file order; links and years are optional.

```markdown
## [Project name](https://example.com)
2026

A short description.
```

Page layout lives in `templates/index.html`; styling lives in `style.css`.
`index.html` and `index.md` are generated—don’t edit them directly.

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npx wrangler dev
```

Keep the virtual environment active. Wrangler rebuilds automatically.
For a standalone build, run `python scripts/build_site.py`.

## Profile activity

`python scripts/update_stats.py` refreshes public GitHub events, Bluesky
posts/reposts, and Meta posts/likes. GitHub Actions runs it daily.
Failed requests retain the previous dates. The browser displays their age
in local time; Markdown uses the last refresh time.

## Markdown

Visit `/index.md`, or request the homepage with `Accept: text/markdown`:

```sh
curl -H 'Accept: text/markdown' http://localhost:8787/
```

## Check and deploy

```sh
python -m unittest test_site.py
node --test test_worker.mjs
npx wrangler deploy
```

Deployment rebuilds the pages. Install `requirements.txt` first in CI.
Only public assets are uploaded; source files are excluded by `.assetsignore`.
