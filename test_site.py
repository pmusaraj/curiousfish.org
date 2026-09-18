from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import activity_age, build, parse_timestamp, render_items, render_site
import update_stats


class PersonalSiteTest(unittest.TestCase):
    def test_generated_pages_are_current(self):
        html, md = render_site()
        self.assertEqual((ROOT / "index.html").read_text(), html)
        self.assertEqual((ROOT / "index.md").read_text(), md)
        self.assertEqual(html.count("<section "), 1)
        self.assertIn("New &amp; Notable", html)
        self.assertIn("🇦🇱", html)
        self.assertIn("🇨🇦", html)
        self.assertIn('<script src="theme.js"></script>', html)

    def test_markdown_items_optional_fields_order_and_formatting(self):
        html = render_items("""## [First](https://example.com)
2026

A **bold** description with [a link](https://example.com/more).

Second paragraph.

## Second & last

No date or link.
""")
        self.assertLess(html.index("First"), html.index("Second &amp; last"))
        self.assertEqual(html.count("<li>"), 2)
        self.assertEqual(html.count("<time "), 1)
        self.assertIn('<time datetime="2026">2026</time>', html)
        self.assertIn('<a href="https://example.com">First</a>', html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<p>Second paragraph.</p>", html)
        self.assertIn('href="https://example.com/more"', html)

    def test_invalid_content_does_not_overwrite_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notable.md").write_text("Forgot a heading")
            (root / "profile-stats.json").write_text((ROOT / "profile-stats.json").read_text())
            (root / "templates").mkdir()
            (root / "templates/index.html").write_text((ROOT / "templates/index.html").read_text())
            (root / "index.html").write_text("previous page")
            with self.assertRaises(ValueError):
                build(root)
            self.assertEqual((root / "index.html").read_text(), "previous page")

    def test_content_and_stats_edits_reach_both_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "templates").mkdir()
            (root / "templates/index.html").write_text((ROOT / "templates/index.html").read_text())
            (root / "notable.md").write_text("## New thing\n2027\n\nFresh content.")
            (root / "profile-stats.json").write_text(json.dumps({"updated_at": "2026-09-17T23:00:00Z", "github_last_activity": "2026-09-17T10:00:00Z", "bluesky_last_activity": "2026-09-16T10:00:00Z", "meta_last_activity": "2026-09-15T10:00:00Z"}))
            build(root)
            for filename in ["index.html", "index.md"]:
                result = (root / filename).read_text()
                for value in ["New thing", "2027", "Fresh content.", "today", "yesterday", "2 days ago"]:
                    self.assertIn(value, result)
                self.assertNotIn("Discourse Free", result)

    def test_activity_age_handles_singular_utc_boundaries_and_unknown(self):
        now = parse_timestamp("2026-09-17T01:00:00Z")
        self.assertEqual(activity_age("2026-09-17T00:00:00Z", now), "today")
        self.assertEqual(activity_age("2026-09-16T23:59:00Z", now), "yesterday")
        self.assertEqual(activity_age("2026-09-16T23:59:00-04:00", now), "today")
        self.assertEqual(activity_age("2026-09-15T12:00:00Z", now), "2 days ago")
        self.assertEqual(activity_age(None, now), "Unknown")
        with self.assertRaises(ValueError):
            parse_timestamp("2026-09-17T01:00:00")

    def test_activity_feeds_use_latest_event_and_repost_time(self):
        old, recent = "2026-09-10T12:00:00Z", "2026-09-17T12:00:00Z"
        self.assertEqual(update_stats.latest_activity("github", [{"created_at": old}, {"created_at": recent}]), recent)
        self.assertEqual(update_stats.latest_activity("github", []), None)
        feed = {"feed": [
            {"post": {"record": {"createdAt": old}}, "reason": {"$type": "app.bsky.feed.defs#reasonRepost", "indexedAt": recent}},
            {"post": {"record": {"createdAt": "2026-09-18T00:00:00Z"}}, "reason": {"$type": "app.bsky.feed.defs#reasonPin"}},
        ]}
        self.assertEqual(update_stats.latest_activity("bluesky", feed), recent)
        self.assertEqual(update_stats.latest_activity("bluesky", {"feed": [{"post": {"record": {"createdAt": old}}}]}), old)
        self.assertEqual(update_stats.latest_activity("meta", {"user_actions": [{"created_at": old}, {"created_at": recent}]}), recent)

    def test_activity_preserves_failed_empty_and_older_results(self):
        old, recent = "2026-09-10T12:00:00Z", "2026-09-17T12:00:00Z"
        for results in [[recent, urllib.error.URLError("offline"), None], [recent, old, old]]:
            with self.subTest(results=results), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "profile-stats.json"
                path.write_text(json.dumps({"github_last_activity": old, "bluesky_last_activity": recent, "meta_last_activity": recent}))
                with patch.object(update_stats, "ROOT", root), patch.object(update_stats, "build") as rebuild, patch.object(
                    update_stats, "fetch_activity", side_effect=results
                ):
                    update_stats.main()
                saved = json.loads(path.read_text())
                for profile in ["github", "bluesky", "meta"]:
                    self.assertEqual(saved[f"{profile}_last_activity"], recent)
                parse_timestamp(saved["updated_at"])
                rebuild.assert_called_once_with(root)

    def test_only_public_assets_uploaded(self):
        allowlist = {line for line in (ROOT / ".assetsignore").read_text().splitlines() if line.startswith("!")}
        self.assertEqual(allowlist, {"!index.html", "!index.md", "!style.css", "!theme.js", "!activity.js", "!images/", "!images/**"})


if __name__ == "__main__":
    unittest.main()
