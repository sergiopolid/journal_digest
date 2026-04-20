#!/usr/bin/env python3
"""
AUTOMATED RESEARCH PIPELINE - Non-interactive, GitHub Actions compatible
"""

import os
import json
from datetime import datetime, timedelta
from anthropic import Anthropic
import requests
import feedparser
import re

# Configuration
notion_api_key = os.environ.get('NOTION_API_KEY')
notion_db_id = "1e900b67c75142a9b06da4e5b512aa38"
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

anthropic_client = Anthropic(api_key=anthropic_key)

JOURNALS = {
    'NEJM': 'https://www.nejm.org/action/showFeed?jc=nejmoa&type=etoc&feed=rss',
    'Chest': 'https://www.atsjournals.org/rss/chest/current.xml',
    'AJRCCM': 'https://www.atsjournals.org/rss/ajrccm/current.xml',
    'Lancet Respiratory': 'https://www.thelancet.com/rssfeed/lanres_current.xml',
    'Thorax': 'https://thorax.bmj.com/rss/current.xml',
    'ERJ': 'https://erj.ersjournals.com/rss/current.xml',
    'Critical Care': 'https://ccforum.biomedcentral.com/articles/most-recent/feed',
}

KEYWORDS_HIGH = ['ra-ild', 'rheumatoid', 'jak inhibitor', 'nintedanib',
                 'pirfenidone', 'interstitial lung', 'pulmonary fibrosis']
KEYWORDS_MEDIUM = ['hemodynamic', 'critical care', 'ards', 'coagulopathy',
                   'mechanical ventilation', 'sepsis', 'vasopressor']

HEADERS = {'User-Agent': 'Mozilla/5.0 (research pipeline; contact: spoli@bwh.harvard.edu)'}


def fetch_articles():
    articles = []
    cutoff = datetime.now() - timedelta(days=7)

    for journal, url in JOURNALS.items():
        try:
            print(f"  Fetching {journal}...")
            feed = feedparser.parse(url, request_headers=HEADERS)
            count = 0
            for entry in feed.entries[:15]:
                try:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') and entry.published_parsed else datetime.now()
                    if published < cutoff:
                        continue
                    articles.append({
                        'title': getattr(entry, 'title', 'Unknown'),
                        'journal': journal,
                        'link': getattr(entry, 'link', ''),
                        'date': published.strftime('%Y-%m-%d'),
                        'summary': getattr(entry, 'summary', '')[:300],
                    })
                    count += 1
                except:
                    continue
            print(f"    → {count} articles")
        except Exception as e:
            print(f"    → Failed: {e}")

    # Deduplicate by title
    seen, unique = set(), []
    for a in articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique.append(a)
    return unique


def score_article(article):
    text = (article['title'] + ' ' + article['summary']).lower()
    if any(kw in text for kw in KEYWORDS_HIGH):
        return 'high'
    if any(kw in text for kw in KEYWORDS_MEDIUM):
        return 'medium'
    return 'low'


def generate_summary(article):
    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-5",  # Fixed model name
            max_tokens=1024,
            messages=[{"role": "user", "content": f"""You are a clinical expert in pulmonary medicine and critical care.

Article: {article['title']}
Journal: {article['journal']}
Abstract: {article['summary']}

Generate:
## Summary
3-4 sentence summary of main findings.

## Clinical Pearls
- Pearl 1
- Pearl 2
- Pearl 3
- Pearl 4
- Pearl 5
"""}]
        )
        text = response.content[0].text
        summary = re.search(r'## Summary\n(.*?)\n## Clinical Pearls', text, re.DOTALL)
        pearls = re.search(r'## Clinical Pearls\n(.*?)(?:\n##|$)', text, re.DOTALL)
        return (summary.group(1).strip() if summary else ""), (pearls.group(1).strip() if pearls else "")
    except Exception as e:
        print(f"    Claude error: {e}")
        return "", ""


def push_to_notion(article, summary, pearls, relevance):
    if not notion_api_key:
        print("    No Notion key, skipping")
        return None
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": notion_db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": article['title'][:100]}}]},
            "Journal": {"rich_text": [{"text": {"content": article['journal']}}]},
            "DOI/Link": {"url": article['link'] or None},
            "Date Discovered": {"date": {"start": article['date']}},
            "Relevance": {"select": {"name": relevance.capitalize()}},
        },
        "children": [
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Summary"}}]}},
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": summary}}]}},
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Clinical Pearls"}}]}},
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": pearls}}]}},
        ]
    }
    try:
        r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data, timeout=15)
        if r.status_code == 200:
            return r.json()['id']
        else:
            print(f"    Notion error {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"    Notion exception: {e}")
        return None


def create_obsidian_note(article, summary, pearls, relevance):
    """Write .md file to local folder — committed back to repo by workflow"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    safe_title = re.sub(r'[^\w\s-]', '', article['title'])[:50].strip()
    specialty = 'RA-ILD' if any(k in article['title'].lower() for k in ['ra-ild', 'rheumatoid', 'ild']) else 'Critical-Care' if 'critical' in article['title'].lower() else 'Pulmonary'

    folder = os.path.join('obsidian_notes', 'Literature', specialty)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{date_str} - {safe_title}.md")
    content = f"""---
journal: "{article['journal']}"
date_published: "{article['date']}"
date_added: "{date_str}"
relevance: "{relevance}"
link: "{article['link']}"
tags: [clinical-pearls, {specialty.lower()}, literature-review]
---

# {article['title']}

## Summary
{summary}

## Clinical Pearls
{pearls}

---
**Source**: {article['journal']} | **Date**: {article['date']}
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath


def main():
    print("=" * 60)
    print("🚀 AUTOMATED RESEARCH PIPELINE")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # 1. Fetch
    print("\n📰 Fetching articles...")
    articles = fetch_articles()
    print(f"→ {len(articles)} unique articles found")

    if not articles:
        print("No articles found this week. Exiting.")
        return

    # 2. Score and filter — only process high + medium relevance
    to_process = [(a, score_article(a)) for a in articles]
    to_process = [(a, s) for a, s in to_process if s in ('high', 'medium')]
    print(f"\n🎯 {len(to_process)} articles marked high/medium relevance")

    if not to_process:
        print("No relevant articles this week.")
        return

    # 3. Process each
    notes_created = []
    notion_created = 0

    for i, (article, relevance) in enumerate(to_process, 1):
        print(f"\n[{i}/{len(to_process)}] {article['title'][:60]}...")
        print(f"  Journal: {article['journal']} | Relevance: {relevance}")

        # Generate summary
        print("  Generating summary with Claude...")
        summary, pearls = generate_summary(article)

        # Push to Notion
        print("  Pushing to Notion...")
        notion_id = push_to_notion(article, summary, pearls, relevance)
        if notion_id:
            notion_created += 1
            print(f"  ✅ Notion: {notion_id}")
        else:
            print("  ⚠️  Notion failed")

        # Create Obsidian note
        filepath = create_obsidian_note(article, summary, pearls, relevance)
        notes_created.append(filepath)
        print(f"  ✅ Note: {filepath}")

    # 4. Summary
    print(f"\n{'='*60}")
    print(f"✅ PIPELINE COMPLETE")
    print(f"   Articles processed: {len(to_process)}")
    print(f"   Notion entries: {notion_created}")
    print(f"   Obsidian notes: {len(notes_created)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
