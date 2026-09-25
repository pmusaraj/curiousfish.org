#!/usr/bin/env python3
"""Read album metadata from the public playlist's embedded page data."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
PLAYLIST_URL = "https://music.apple.com/ca/playlist/on-rotation/pl.u-38oW9zeIRrvzg"
PLAYLIST_ID = "pl.u-38oW9zeIRrvzg"


class PageData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.capture = dict(attrs).get("id") == "serialized-server-data"

    def handle_endtag(self, tag):
        if tag == "script":
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)


def public_url(value, artwork=False):
    url = urlsplit(value)
    host = url.hostname or ""
    allowed = host.endswith(".mzstatic.com") if artwork else host == "music.apple.com"
    if url.scheme != "https" or not allowed or url.username or url.password:
        raise ValueError("Unexpected music metadata URL")
    return value


def parse_playlist(html):
    parser = PageData()
    parser.feed(html)
    data = json.loads("".join(parser.parts))
    pages = [entry["data"] for entry in data["data"]
             if entry.get("intent", {}).get("contentDescriptor", {}).get("identifiers", {}).get("storeAdamID") == PLAYLIST_ID]
    if len(pages) != 1:
        raise ValueError("Expected public playlist data was not found")
    sections = pages[0]["sections"]
    tracks = [item for section in sections if section.get("itemKind") == "trackLockup"
              for item in section["items"]]
    # Empty/incomplete pages can be an Apple error or a visibility change.
    # Preserve the snapshot instead of silently clearing the website.
    if not tracks:
        raise ValueError("No public tracks found; keeping the previous albums")
    albums = []
    for track in tracks:
        links = [(link, link.get("segue", {}).get("destination", {}).get("contentDescriptor", {}))
                 for link in track.get("tertiaryLinks", [])]
        match = next(((link, desc) for link, desc in links if desc.get("kind") == "album"), None)
        if not match:
            raise ValueError("A playlist track is missing album metadata")
        link, descriptor = match
        album_id = descriptor["identifiers"]["storeAdamID"]
        artwork = track["artwork"]["dictionary"]["url"]
        for key, value in {"w": "400", "h": "400", "f": "jpg", "c": "bb"}.items():
            artwork = artwork.replace("{" + key + "}", value)
        if "{" in artwork:
            raise ValueError("Unrecognized artwork template")
        album = {"id": album_id, "title": link["title"], "artist": track["artistName"],
                 "url": public_url(descriptor["url"]), "artwork": public_url(artwork, artwork=True)}
        if not album["title"] or not album["artist"]:
            raise ValueError("Missing album title or artist")
        albums.append(album)
    return {"playlist_url": PLAYLIST_URL, "albums": albums}


def refresh(root=ROOT):
    request = Request(PLAYLIST_URL, headers={"User-Agent": "curiousfish-music/1.0", "Accept-Language": "en-CA,en;q=0.9"})
    with urlopen(request, timeout=30) as response:
        snapshot = parse_playlist(response.read().decode("utf-8"))
    path = root / "on-rotation.json"
    content = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if not path.exists() or path.read_text() != content:
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(content)
        temporary.replace(path)
    print(f"On rotation: {len(snapshot['albums'])} albums")


if __name__ == "__main__":
    try:
        refresh()
    except Exception as error:
        print(f"Music refresh failed; previous snapshot preserved: {error}", file=sys.stderr)
        sys.exit(1)
