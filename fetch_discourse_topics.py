#!/usr/bin/env python3
"""
Fetch notable Discourse Meta topics and generate portfolio updates.

This script extracts your recent topics from meta.discourse.org and creates
a PR to update your portfolio site with notable items.

Usage:
    python3 fetch_discourse_topics.py

Note: Due to Discourse API structure, this script uses manual topic data.
Update the TOPICS list below with your actual recent topics.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
PORTFOLIO_PATH = Path("/Users/pmusaraj/Projects/forks/curiousfish.org")
DISCOURSE_BASE = "https://meta.discourse.org"

# Manual topic data - update with your actual recent topics
# Format: title, id, replies, views, date (ISO format), tags
TOPICS = [
    {
        "title": "Verso Theme",
        "id": None,  # Update with actual topic ID
        "reply_count": 0,
        "views": 41,
        "created_at": "2026-04-27",
        "tags": ["theme", "customization"],
        "category": "Customization",
        "description": "Development of the Verso theme for Discourse, a modern and customizable theme."
    },
    {
        "title": "Buffer – streamline sharing topics on social media",
        "id": None,
        "reply_count": 0,
        "views": 57,
        "created_at": "2026-04-16",
        "tags": ["experimental", "plugin"],
        "category": "Contribute",
        "description": "Plugin to streamline sharing Discourse topics on social media platforms."
    },
    {
        "title": "Introducing image grids in posts",
        "id": None,
        "reply_count": 43,
        "views": 7400,
        "created_at": "2026-01-10",
        "tags": ["new-feature", "megaphone"],
        "category": "News and Events",
        "description": "New feature announcement for image grids in Discourse posts, allowing better visual organization."
    }
]

# Criteria for notable topics
MIN_REPLIES = 10
MIN_VIEWS = 500
IMPORTANT_TAGS = ["new-feature", "official", "release-notes", "megaphone"]

def is_notable(topic):
    """Check if a topic meets notable criteria."""
    if topic["reply_count"] >= MIN_REPLIES:
        return True
    if topic["views"] >= MIN_VIEWS:
        return True
    if any(tag in IMPORTANT_TAGS for tag in topic["tags"]):
        return True
    return False

def format_date(date_str):
    """Format date string for display."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%B %d, %Y")
    except:
        return date_str

def generate_entry(topic):
    """Generate a markdown entry for a topic."""
    title = topic["title"]
    topic_id = topic["id"] or "unknown"
    reply_count = topic["reply_count"]
    views = topic["views"]
    created_at = format_date(topic["created_at"])
    tags = topic["tags"]
    description = topic.get("description", "")
    
    url = f"{DISCOURSE_BASE}/t/{topic_id}" if topic_id != "unknown" else "#"
    
    entry = f"""### {title}

**Posted:** {created_at}  
**Link:** [{url}]({url})  
**Engagement:** {reply_count} replies, {views} views  
**Category:** {topic['category']}  
**Tags:** {', '.join(tags) if tags else 'None'}

{description}

"""
    return entry

def main():
    print("Processing notable Discourse Meta topics...")
    
    # Filter notable topics
    notable_topics = [t for t in TOPICS if is_notable(t)]
    
    if not notable_topics:
        print("No notable topics found matching criteria.")
        print(f"Criteria: >= {MIN_REPLIES} replies OR >= {MIN_VIEWS} views OR tags: {IMPORTANT_TAGS}")
        return
    
    print(f"Found {len(notable_topics)} notable topics:")
    for topic in notable_topics:
        print(f"  - {topic['title']} ({topic['reply_count']} replies, {topic['views']} views)")
    
    # Generate markdown content
    entries = []
    for topic in notable_topics:
        entries.append(generate_entry(topic))
    
    content = "# Recent Discourse Work\n\n"
    content += "Notable topics and announcements from [meta.discourse.org](https://meta.discourse.org):\n\n"
    content += "---\n\n"
    content += "\n---\n\n".join(entries)
    
    # Save to file
    output_file = PORTFOLIO_PATH / "recent-work.md"
    output_file.write_text(content)
    
    print(f"\nGenerated content saved to: {output_file}")
    print("\nPreview:")
    print("=" * 60)
    print(content[:1000])
    print("=" * 60)
    
    # Check if git repo and create branch
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=PORTFOLIO_PATH,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"update-portfolio-{timestamp}"
        
        print(f"\nCreating git branch: {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=PORTFOLIO_PATH, check=True)
        subprocess.run(["git", "add", "recent-work.md"], cwd=PORTFOLIO_PATH, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add recent Discourse work: {len(notable_topics)} notable topics"],
            cwd=PORTFOLIO_PATH,
            check=True
        )
        print("Changes committed. Ready to push and create PR.")
        print(f"\nTo complete, run:")
        print(f"  cd {PORTFOLIO_PATH}")
        print(f"  git push origin {branch_name}")
        print(f"  gh pr create --title 'Update portfolio with recent Discourse work' --body 'Added {len(notable_topics)} notable topics from meta.discourse.org'")
    else:
        print("\nNot a git repository. Manual steps required.")

if __name__ == "__main__":
    main()
