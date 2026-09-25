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
posts/reposts, and Meta posts/likes. GitHub Actions runs it every two days.
Failed requests retain the previous dates. The browser displays their age
in local time; Markdown uses the last refresh time.

## Markdown

Visit `/index.md`, or request the homepage with `Accept: text/markdown`:

```sh
curl -H 'Accept: text/markdown' http://localhost:8787/
```

## Check and deploy

```sh
python -m unittest test_site.py test_music.py
node --test test_worker.mjs
npx wrangler deploy
```

Deployment rebuilds the pages. Install `requirements.txt` first in CI.
Only public assets are uploaded; source files are excluded by `.assetsignore`.

## On rotation

The homepage shows album artwork for all tracks available on the public
[On Rotation playlist](https://music.apple.com/ca/playlist/on-rotation/pl.u-38oW9zeIRrvzg),
in reverse playlist order (newest additions first), including repeated albums. Add songs or albums to the end of that playlist to feature them. This is a curated selection, not automatic listening history.

```sh
python scripts/update_music.py
python scripts/build_site.py
```

The refresh reads album names, artists, links, and artwork URLs from Apple's
public page into `on-rotation.json`. No Apple credentials are needed. The existing
GitHub Action refreshes this data every two days and rebuilds HTML and Markdown.
Artwork loads from Apple's image CDN. The JSON is build input, not a public asset.

This uses embedded page JSON, an undocumented format that Apple may change.
Only tracks included in the public page are considered; keep featured albums
at the end of the publicly available playlist. Failed, unrecognized, or empty responses preserve
the last successful snapshot and flag the workflow as failed after committing
other updates. To intentionally clear the section, set `albums` to `[]` in the
snapshot and disable its refresh. Updates reach the live site on its next deploy.
Run music checks with `python -m unittest test_music.py`.
