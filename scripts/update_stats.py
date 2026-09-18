#!/usr/bin/env python3
"""Refresh public profile activity timestamps, then rebuild HTML and Markdown."""
from datetime import datetime, timezone
from pathlib import Path
import json
import urllib.error
import urllib.request

from build_site import build, parse_timestamp

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "github": "https://api.github.com/users/pmusaraj/events/public?per_page=100",
    "bluesky": "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=musaraj.com&filter=posts_with_replies&limit=100&includePins=false",
    "meta": "https://meta.discourse.org/user_actions.json?username=pmusaraj&filter=1,4,5&limit=50",
}


def latest_activity(profile: str, data) -> str | None:
    if profile == "github":
        timestamps = [event["created_at"] for event in data]
    elif profile == "bluesky":
        timestamps = []
        for entry in data["feed"]:
            reason = entry.get("reason", {})
            if reason.get("$type") == "app.bsky.feed.defs#reasonPin":
                continue
            if reason.get("$type") == "app.bsky.feed.defs#reasonRepost":
                timestamps.append(reason["indexedAt"])
            else:
                timestamps.append(entry["post"]["record"]["createdAt"])
    elif profile == "meta":
        timestamps = [action["created_at"] for action in data["user_actions"]]
    else:
        raise ValueError(f"Unknown profile: {profile}")
    dates = [parse_timestamp(value) for value in timestamps]
    return max(dates).isoformat().replace("+00:00", "Z") if dates else None


def fetch_activity(profile: str, url: str) -> str | None:
    request = urllib.request.Request(url, headers={"User-Agent": "curiousfish-activity/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return latest_activity(profile, json.load(response))


def main() -> None:
    stats_file = ROOT / "profile-stats.json"
    previous = json.loads(stats_file.read_text())
    stats = {"updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    for profile, url in SOURCES.items():
        key = f"{profile}_last_activity"
        stats[key] = previous.get(key)
        try:
            latest = fetch_activity(profile, url)
            # Empty feeds (including GitHub's limited event window) must not
            # erase a known date or claim the user was just active.
            if latest and (not stats[key] or parse_timestamp(latest) > parse_timestamp(stats[key])):
                stats[key] = latest
        except (urllib.error.URLError, TimeoutError, KeyError, TypeError, ValueError) as error:
            print(f"Keeping previous {key}: {error}")
    stats_file.write_text(json.dumps(stats, indent=2) + "\n")
    build(ROOT)


if __name__ == "__main__":
    main()
