#!/usr/bin/env python3
"""Update the stats cards in index.html.

This is intentionally the only automation for the site. The page itself is plain
HTML/CSS; edit index.html and style.css directly for everything else.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
import json
import os
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

FALLBACK = {
    "bluesky": {"followsCount": 246, "followersCount": 104, "postsCount": 59},
    "github": {"public_repos": 102, "commits_total": 4710, "reviews_total": 3517},
    "meta_summary": {"post_count": 4795, "likes_received": 11207, "days_visited": 3125},
}


def fetch_json(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
    request_headers = {"User-Agent": "curiousfish-stats/1.0"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def count(value: int | str | None) -> str:
    if value is None:
        return "0"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def stat(label: str, value: int | str | None) -> str:
    return f'''          <div class="stat">
            <strong>{count(value)}</strong>
            <span>{escape(label)}</span>
          </div>'''


def replace_card_stats(html: str, card_class: str, stats: list[tuple[str, int | str | None]]) -> str:
    pattern = re.compile(
        rf'(<a class="stats-card {re.escape(card_class)}"[\s\S]*?<div class="stats-row {re.escape(card_class)}-stats">\n)'
        rf'[\s\S]*?'
        rf'(\n        </div>\n      </a>)',
        re.MULTILINE,
    )
    replacement = r"\1" + "\n".join(stat(label, value) for label, value in stats) + r"\2"
    html, replacements = pattern.subn(replacement, html, count=1)
    if replacements != 1:
        raise RuntimeError(f"Could not find stats card: {card_class}")
    return html


def github_contribution_stats(created_at: str | None) -> dict[str, int]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return FALLBACK["github"]

    now = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        start = datetime.fromisoformat((created_at or "2009-01-01T00:00:00Z").replace("Z", "+00:00"))
    except ValueError:
        start = datetime(2009, 1, 1, tzinfo=timezone.utc)

    query = """
    query($user: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $user) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """

    totals = {"commits_total": 0, "reviews_total": 0}
    window_start = start
    while window_start < now:
        window_end = min(window_start + timedelta(days=365), now)
        payload = json.dumps(
            {
                "query": query,
                "variables": {
                    "user": "pmusaraj",
                    "from": window_start.isoformat().replace("+00:00", "Z"),
                    "to": window_end.isoformat().replace("+00:00", "Z"),
                },
            }
        ).encode()
        data = fetch_json(
            "https://api.github.com/graphql",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        if data.get("errors"):
            raise RuntimeError(data["errors"])
        collection = data["data"]["user"]["contributionsCollection"]
        totals["commits_total"] += collection.get("totalCommitContributions", 0)
        totals["reviews_total"] += collection.get("totalPullRequestReviewContributions", 0)
        window_start = window_end + timedelta(seconds=1)
    return totals


def main() -> None:
    try:
        bluesky = fetch_json("https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=musaraj.com")
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        bluesky = FALLBACK["bluesky"]

    try:
        github_profile = fetch_json("https://api.github.com/users/pmusaraj")
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        github_profile = FALLBACK["github"]

    created_at = github_profile.get("created_at")
    if not isinstance(created_at, str):
        created_at = None
    try:
        github_contributions = github_contribution_stats(created_at)
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, RuntimeError):
        github_contributions = FALLBACK["github"]
    github = {**FALLBACK["github"], **github_profile, **github_contributions}

    try:
        meta_summary = fetch_json("https://meta.discourse.org/u/pmusaraj/summary.json").get("user_summary", {})
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
        meta_summary = FALLBACK["meta_summary"]
    meta_summary = {**FALLBACK["meta_summary"], **meta_summary}

    html = INDEX.read_text()
    html = replace_card_stats(
        html,
        "bluesky-card",
        [
            ("Following", bluesky.get("followsCount")),
            ("Followers", bluesky.get("followersCount")),
            ("Posts", bluesky.get("postsCount")),
        ],
    )
    html = replace_card_stats(
        html,
        "github-card",
        [
            ("Repos", github.get("public_repos")),
            ("Commits", github.get("commits_total")),
            ("PR reviews", github.get("reviews_total")),
        ],
    )
    html = replace_card_stats(
        html,
        "meta-card",
        [
            ("Posts", meta_summary.get("post_count")),
            ("Likes", meta_summary.get("likes_received")),
            ("Days", meta_summary.get("days_visited")),
        ],
    )
    INDEX.write_text(html)


if __name__ == "__main__":
    main()
