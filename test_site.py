from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "index.html").read_text()
CSS = (ROOT / "style.css").read_text()
README = (ROOT / "README.md").read_text()
WRANGLER = (ROOT / "wrangler.jsonc").read_text()
ASSETSIGNORE = (ROOT / ".assetsignore").read_text()
STATS_SCRIPT = (ROOT / "scripts" / "update_stats.py").read_text()
WORKFLOW = (ROOT / ".github" / "workflows" / "update-stats.yml").read_text()


class PersonalSiteTest(unittest.TestCase):
    def test_site_is_plain_html_and_css(self):
        self.assertIn("Penar Musaraj", HTML)
        self.assertIn("curiousfish.org / musaraj.com", HTML)
        self.assertIn('Current role: Engineering manager at <a href="https://www.discourse.org">Discourse</a>', HTML)
        self.assertNotIn("Penar Musaraj's home on the web", HTML)
        self.assertIn("Play", HTML)
        self.assertIn("Work", HTML)
        self.assertIn('<link rel="stylesheet" href="style.css">', HTML)
        self.assertNotIn('<script', HTML.lower())
        self.assertNotIn('<nav class="links"', HTML)
        self.assertNotIn("google-analytics.com/ga.js", HTML)
        self.assertNotIn('id="bg"', HTML)

    def test_manual_sections_live_in_index_html(self):
        self.assertIn("Led implementation and launch of the Free plan", HTML)
        self.assertIn("Discourse ID", HTML)
        self.assertIn("https://discover.discourse.com", HTML)
        self.assertIn("Passkeys, image grids, SVG icons", HTML)
        for project in [
            "Discourse theme screenshots",
            "Hey, what’s on TV?",
            "Discourse Right Sidebar Blocks",
        ]:
            self.assertIn(project, HTML)
        self.assertLess(HTML.index("Work"), HTML.index("Play"))

    def test_profile_stats_are_present_and_script_updateable(self):
        match = re.search(r'<section class="section social-stats".*?</section>', HTML, re.S)
        self.assertIsNotNone(match)
        section = match.group(0)
        for text in ["Bluesky", "GitHub", "Discourse Meta"]:
            self.assertIn(text, section)
        for label in ["Following", "Followers", "Repos", "Commits", "PR reviews", "Posts", "Likes", "Days"]:
            self.assertIn(label, section)
        for icon in ["images/social-bluesky.png", "images/social-github.png", "images/social-discourse-meta.jpg"]:
            self.assertIn(icon, section)
            self.assertTrue((ROOT / icon).exists(), icon)
        self.assertNotIn("www.google.com/s2/favicons", section)
        self.assertIn("replace_card_stats", STATS_SCRIPT)
        self.assertIn("public.api.bsky.app", STATS_SCRIPT)
        self.assertIn("api.github.com/graphql", STATS_SCRIPT)
        self.assertIn("meta.discourse.org/u/pmusaraj/summary.json", STATS_SCRIPT)

    def test_github_action_updates_stats_every_two_days(self):
        self.assertIn('cron: "0 8 */2 * *"', WORKFLOW)
        self.assertIn("python scripts/update_stats.py", WORKFLOW)
        self.assertIn("contents: write", WORKFLOW)
        self.assertIn("git commit -m \"Update profile stats\"", WORKFLOW)

    def test_no_build_step_documented_or_required(self):
        self.assertIn("There is no build step", README)
        self.assertIn("wrangler deploy", README)
        self.assertNotIn("build_site.py", README)
        self.assertNotIn("python3 build_site.py", README)
        self.assertIn('"directory": "."', WRANGLER)
        self.assertNotIn('"directory": "./dist"', WRANGLER)
        self.assertIn("*", ASSETSIGNORE)
        self.assertIn("!index.html", ASSETSIGNORE)
        self.assertIn("!style.css", ASSETSIGNORE)
        self.assertIn("!images/**", ASSETSIGNORE)

    def test_worker_allowlists_public_paths(self):
        worker = (ROOT / "worker.js").read_text()
        self.assertIn('url.pathname === "/"', worker)
        self.assertIn('url.pathname === "/index.html"', worker)
        self.assertIn('url.pathname === "/style.css"', worker)
        self.assertIn('url.pathname.startsWith("/images/")', worker)
        self.assertIn('return new Response("Not found"', worker)


if __name__ == "__main__":
    unittest.main()
