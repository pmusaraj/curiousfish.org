#!/usr/bin/env python3
"""Render notable.md into the static homepage and its Markdown representation."""
from html import escape, unescape
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import json
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]


def parse_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Activity timestamps must include a timezone")
    return timestamp.astimezone(timezone.utc)


def activity_age(value: str | None, as_of: datetime) -> str:
    if not value:
        return "Unknown"
    days = max(0, (as_of.astimezone(timezone.utc).date() - parse_timestamp(value).date()).days)
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    return f"{days} days ago"


def activity_html(value: str | None, label: str) -> str:
    if not value:
        return '<span class="stat" title="Last activity" aria-label="Last activity: unknown">Unknown</span>'
    return (f'<time class="stat" datetime="{escape(value, quote=True)}" title="Last activity" '
            f'aria-label="Last activity: {escape(label)}">{escape(label)}</time>')


def render_items(source: str) -> str:
    """Each H2 starts an item; an optional first four-digit line is its year."""
    chunks = re.split(r"^##[ \t]+", source.strip(), flags=re.MULTILINE)
    if chunks[0].strip() or len(chunks) < 2:
        raise ValueError("notable.md must start with a ## heading for each item")
    items = []
    for chunk in chunks[1:]:
        lines = chunk.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not title:
            raise ValueError("Each item needs a title")
        year = ""
        first, _, rest = body.partition("\n")
        if re.fullmatch(r"\d{4}", first):
            year = f'<time datetime="{first}">{first}</time>'
            body = rest.strip()
        # Content is trusted, repository-authored Markdown, like the HTML template.
        title_html = markdown.markdown(title)
        if not (title_html.startswith("<p>") and title_html.endswith("</p>")):
            raise ValueError(f"Invalid item heading: {title}")
        title_html = title_html[3:-4]
        link = re.search(r'<a href="([^"]+)"', title_html)
        if link:
            host = urlsplit(unescape(link[1])).hostname
            icon = "social-github.png" if host in {"github.com", "www.github.com"} else "globe.svg"
            title_html = f'<img class="project-icon" src="images/{icon}" alt="">' + title_html
        body_html = markdown.markdown(body)
        items.append(
            f'        <li>\n          <p class="project-title">{title_html}{year}</p>\n'
            f'          <div class="description">{body_html}</div>\n        </li>'
        )
    return "\n".join(items)


def render_site(root: Path = ROOT) -> tuple[str, str]:
    source = (root / "notable.md").read_text()
    stats = json.loads((root / "profile-stats.json").read_text())
    as_of = parse_timestamp(stats["updated_at"])
    values = {profile: activity_age(stats.get(f"{profile}_last_activity"), as_of)
              for profile in ("github", "bluesky", "meta")}
    template = (root / "templates/index.html").read_text()
    substitutions = {f"{profile}_activity": activity_html(stats.get(f"{profile}_last_activity"), label)
                     for profile, label in values.items()}
    substitutions["notable_items"] = render_items(source)
    music_html, music_md = render_music(root)
    substitutions["on_rotation"] = music_html
    html = re.sub(r"{{ (\w+) }}", lambda match: substitutions[match[1]], template)
    md = f'''# Penar Musaraj

curiousfish.org / musaraj.com

Engineering manager at [Discourse](https://www.discourse.org).

Based in Montreal.

- [GitHub](https://github.com/pmusaraj) — last activity: {values['github']}
- [Bluesky](https://bsky.app/profile/musaraj.com) — last activity: {values['bluesky']}
- [Discourse Meta](https://meta.discourse.org/u/pmusaraj) — last activity: {values['meta']}

## New & Notable

{re.sub(r'^## ', '### ', source.strip(), flags=re.MULTILINE)}
{music_md}
'''
    return html, md.rstrip() + "\n"


def render_music(root: Path) -> tuple[str, str]:
    path = root / "on-rotation.json"
    if not path.exists():
        return "", ""
    music = json.loads(path.read_text())
    if not music["albums"]:
        return "", ""
    from update_music import public_url
    playlist = public_url(music["playlist_url"])
    cards, lines = [], []
    for album in music["albums"][:12]:
        url = public_url(album["url"])
        artwork = public_url(album["artwork"], artwork=True)
        title, artist = escape(album["title"]), escape(album["artist"])
        cards.append(f'        <li><a href="{escape(url, quote=True)}" aria-label="{title} — {artist}">'
                     f'<span class="album-artist" aria-hidden="true">{artist}</span>'
                     f'<img src="{escape(artwork, quote=True)}" alt="" width="160" height="160" loading="lazy"></a></li>')
        # Escape remote text so it cannot introduce Markdown links or HTML.
        def md_text(value):
            return re.sub(r'([\\`*_{}\[\]()#!|])', r'\\\1', escape(value).replace("\n", " "))
        lines.append(f'- [{md_text(album["title"])}](<{url}>) — {md_text(album["artist"])}')
    html = ('    <section aria-labelledby="rotation-title">\n'
            '      <div class="rotation-heading"><h2 id="rotation-title">On rotation</h2>'
            f'<a href="{escape(playlist, quote=True)}">Listen on Apple Music ↗</a></div>\n'
            '      <div class="album-strip"><ul class="albums">\n' + '\n'.join(cards) + '\n      </ul></div>\n    </section>')
    md = '\n## On rotation\n\n' + '\n'.join(lines) + f'\n\n[Listen on Apple Music]({playlist})\n'
    return html, md


def build(root: Path = ROOT) -> None:
    html, md = render_site(root)
    (root / "index.html").write_text(html)
    (root / "index.md").write_text(md)


if __name__ == "__main__":
    build()
