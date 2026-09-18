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

The homepage shows up to six distinct albums from the public
[On Rotation playlist](https://music.apple.com/ca/playlist/on-rotation/pl.u-38oW9zeIRrvzg),
in playlist order. Add songs or albums to that playlist and put the albums you
want featured first. This is a curated selection, not automatic listening history.

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
near the top of a long playlist. Failed, unrecognized, or empty responses preserve
the last successful snapshot and flag the workflow as failed after committing
other updates. To intentionally clear the section, set `albums` to `[]` in the
snapshot and disable its refresh. Updates reach the live site on its next deploy.
Run music checks with `python -m unittest test_music.py`.

## Apple Music authorization setup (optional; unused by On rotation)

Run `python3 scripts/music_auth.py`, then open <http://127.0.0.1:8765>.
Enter your Apple Developer Team ID and MusicKit Key ID, select the associated
`.p8` file, and click **Prepare sign-in**. Then click **Sign in with Apple Music**
and authorize the Apple Account whose listening history you want to use.
Copy the resulting token into the GitHub Actions secret `APPLE_MUSIC_USER_TOKEN`.

The helper signs a one-hour developer token with browser Web Crypto. It does not
upload or persist the private key. Only the signed developer token is passed to
Apple's MusicKit JS. MusicKit may retain user authorization in browser storage.
The helper binds to loopback and serves only its two assets; it is excluded from
the public site by the existing asset allowlist. Stop it with Ctrl-C when done.
No additional Python dependencies are required. This helper is retained for
future authenticated API experiments; the playlist integration does not use it.
