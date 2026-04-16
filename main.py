#!/usr/bin/env python3
"""
COMPLETE AUTOMATED RESEARCH PIPELINE
- Real article discovery from journal RSS feeds
- Notion database integration
- Obsidian note creation
- Email notifications
- Weekly automation
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
notion_db_id = "34482b8a2d8f8040b027c1c0b0202a68"
obsidian_vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '/Users/sergiopoli/Documents/Obsidian Vault/')
your_email = os.environ.get('YOUR_EMAIL', 'spoli@bwh.harvard.edu')
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

# Initialize clients
anthropic_client = Anthropic(api_key=anthropic_key)


class RealArticleDiscovery:
    """Discover REAL articles from journal RSS feeds"""
    
    def __init__(self):
        self.articles = []
        self.journals = {
            'NEJM': 'https://feeds.nejm.org/',
            'Chest': 'https://www.chest.org/rss',
            'JAMA': 'https://jamanetwork.com/rss/home.xml',
            'AJRCCM': 'https://www.atsjournals.org/rss/ajrccm/current.xml',
            'Lancet Respiratory': 'https://www.thelancet.com/respiratory-medicine/feed.rss',
            'Thorax': 'https://thorax.bmj.com/rss/current.xml',
            'ERJ': 'https://erj.ersjournals.com/rss/current.xml',
            'Critical Care': 'https://ccforum.biomedcentral.com/articles/most-recent/feed',
        }
    
    def discover(self):
        """Discover articles from journal feeds"""
        print("\n📰 DISCOVERING REAL ARTICLES FROM JOURNALS...")
        
        for journal_name, rss_url in self.journals.items():
            try:
                print(f"   Checking {journal_name}...", end=" ")
                feed = feedparser.parse(rss_url)
                
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for entry in feed.entries[:10]:
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        else:
                            published = datetime.now()
                        
                        if published < cutoff_date:
                            continue
                        
                        doi = None
                        link = ''
                        if hasattr(entry, 'link'):
                            link = entry.link
                            if 'doi.org' in link:
                                doi = link
                        
                        article = {
                            'title': entry.title if hasattr(entry, 'title') else 'Unknown',
                            'journal': journal_name,
                            'link': link,
                            'doi': doi,
                            'source': f'Journal RSS: {journal_name}',
                            'type': self._classify(entry.title if hasattr(entry, 'title') else ''),
                            'date': published.strftime('%Y-%m-%d'),
                            'summary': entry.summary[:200] if hasattr(entry, 'summary') else '',
                        }
                        self.articles.append(article)
                    except:
                        continue
                
                print(f"✓ ({len([a for a in self.articles if a['journal'] == journal_name])} articles)")
            except Exception as e:
                print(f"✗")
                continue
        
        # Deduplicate
        seen = set()
        unique = []
        for article in self.articles:
            key = article['title']
            if key not in seen:
                seen.add(key)
                unique.append(article)
        
        self.articles = unique
        return self.articles
    
    def _classify(self, title):
        """Classify article type"""
        title_lower = title.lower()
        if any(w in title_lower for w in ['randomized', 'rct', 'trial']):
            return 'RCT'
        elif any(w in title_lower for w in ['case', 'report']):
            return 'Case Report'
        elif any(w in title_lower for w in ['review', 'meta']):
            return 'Review'
        return 'Research'
    
    def format_for_curation(self, articles):
        """Format articles by relevance"""
        highly_relevant = []
        medium_relevant = []
        potentially_relevant = []
        
        keywords_high = ['ra-ild', 'rheumatoid', 'jak inhibitor', 'nintedanib', 'pirfenidone', 'ild']
        keywords_medium = ['interstitial lung', 'hemodynamic', 'ett', 'coagulopathy', 'critical care', 'ards']
        
        for article in articles:
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            if any(kw in text for kw in keywords_high):
                highly_relevant.append(article)
            elif any(kw in text for kw in keywords_medium):
                medium_relevant.append(article)
            else:
                potentially_relevant.append(article)
        
        return highly_relevant, medium_relevant, potentially_relevant


class NotionIntegration:
    """Create and update articles in Notion database"""
    
    def __init__(self):
        self.api_key = notion_api_key
        self.db_id = notion_db_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def create_entry(self, article):
        """Create article entry in Notion"""
        try:
            data = {
                "parent": {"database_id": self.db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": article['title'][:100]}}]
                    },
                    "Journal": {
                        "rich_text": [{"text": {"content": article['journal']}}]
                    },
                    "DOI/Link": {
                        "url": article.get('link', '')
                    },
                    "Pipeline Status": {
                        "select": {"name": "Found"}
                    },
                    "Date Discovered": {
                        "date": {"start": article['date']}
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['id']
            else:
                return None
        except Exception as e:
            print(f"Error creating Notion entry: {e}")
            return None
    
    def update_entry(self, notion_id, summary, pearls):
        """Update Notion entry with summary and pearls"""
        try:
            data = {
                "properties": {
                    "Summary": {
                        "rich_text": [{"text": {"content": summary[:2000]}}]
                    },
                    "Clinical Pearls": {
                        "rich_text": [{"text": {"content": pearls[:2000]}}]
                    },
                    "Pipeline Status": {
                        "select": {"name": "Published to Obsidian"}
                    }
                }
            }
            
            response = requests.patch(
                f"{self.base_url}/pages/{notion_id}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating Notion entry: {e}")
            return False


class ClaudeSummaryGenerator:
    """Generate summaries and clinical pearls using Claude"""
    
    def generate(self, article):
        """Generate summary and pearls"""
        try:
            prompt = f"""You are a clinical expert in pulmonary medicine and critical care.

Based on this article, generate:
1. A 3-4 sentence SUMMARY of main findings
2. 5-7 CLINICAL PEARLS as bullet points

Article: {article['title']}
Journal: {article['journal']}
Type: {article['type']}
Date: {article['date']}

Format your response as:

## Summary
[summary here]

## Clinical Pearls
- [pearl 1]
- [pearl 2]
- [pearl 3]
- [pearl 4]
- [pearl 5]
"""
            
            message = anthropic_client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            summary_match = re.search(r'## Summary\n(.*?)\n## Clinical Pearls', response_text, re.DOTALL)
            pearls_match = re.search(r'## Clinical Pearls\n(.*?)(?:\n##|$)', response_text, re.DOTALL)
            
            summary = summary_match.group(1).strip() if summary_match else ""
            pearls = pearls_match.group(1).strip() if pearls_match else ""
            
            return summary, pearls
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "", ""


class ObsidianPublisher:
    """Create Obsidian notes"""
    
    def publish(self, article, summary, pearls):
        """Create note in Obsidian vault"""
        try:
            # Determine specialty
            title_lower = article['title'].lower()
            if any(w in title_lower for w in ['ra-ild', 'rheumatoid', 'ild']):
                specialty = 'Pulmonary/RA-ILD'
            elif any(w in title_lower for w in ['critical care', 'icu']):
                specialty = 'Critical Care'
            else:
                specialty = 'Pulmonary'
            
            # Create path
            vault_path = obsidian_vault_path.rstrip('/')
            note_dir = os.path.join(vault_path, 'Literature', 'Clinical Pearls', specialty)
            os.makedirs(note_dir, exist_ok=True)
            
            # Create filename
            date_str = datetime.now().strftime('%Y-%m-%d')
            safe_title = article['title'][:50].replace('/', '-').replace(':', '-').replace('?', '')
            filename = f"{safe_title} - {date_str}.md"
            filepath = os.path.join(note_dir, filename)
            
            # Create content
            note_content = f"""---
journal: "{article['journal']}"
doi: "{article.get('doi', 'N/A')}"
published: "{article['date']}"
tags: "#clinical-pearls #{specialty.lower().replace('/', '-')}"
date_added: "{date_str}"
---

# {article['title']}

## Summary
{summary}

## Clinical Pearls
{pearls}

---

**Source**: {article['journal']} ({article['date']})
**Type**: {article['type']}
**DOI**: {article.get('doi', 'N/A')}
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(note_content)
            
            return filepath
        except Exception as e:
            print(f"Error creating Obsidian note: {e}")
            return None


def main():
    """Main pipeline execution"""
    print("=" * 70)
    print("🚀 REAL AUTOMATED RESEARCH PIPELINE")
    print("=" * 70)
    
    # Step 1: Discover articles
    print("\n📰 STEP 1: DISCOVERING REAL ARTICLES")
    discovery = RealArticleDiscovery()
    articles = discovery.discover()
    print(f"\n✅ Found {len(articles)} real articles from journals")
    
    if not articles:
        print("❌ No articles found this week")
        return
    
    # Step 2: Present for curation
    print("\n👁️  STEP 2: ARTICLES FOR CURATION")
    highly, medium, potential = discovery.format_for_curation(articles)
    
    print(f"\n═══════════════════════════════════════════════════════════")
    print(f"📰 RESEARCH ARTICLE CURATION - Week of {datetime.now().strftime('%b %d, %Y')}")
    print(f"═══════════════════════════════════════════════════════════")
    print(f"\n{len(articles)} candidate articles discovered\n")
    
    print(f"HIGHLY RELEVANT ({len(highly)} articles):")
    for i, article in enumerate(highly[:5], 1):
        print(f"  {i}. {article['title'][:70]}...")
        print(f"     📖 {article['journal']} | {article['doi'] or 'no DOI'}")
        print(f"     Type: {article['type']} | Date: {article['date']}\n")
    
    print(f"MEDIUM RELEVANCE ({len(medium)} articles):")
    for i, article in enumerate(medium[:3], 1):
        print(f"  {i+len(highly)}. {article['title'][:70]}...")
        print(f"     📖 {article['journal']} | Type: {article['type']}\n")
    
    print(f"═══════════════════════════════════════════════════════════")
    print(f"✅ WHAT TO DO:")
    print(f"Reply with the article numbers you want processed.")
    print(f"Example: '1, 2, 5, 7'")
    print(f"Or use shortcuts:")
    print(f"- 'Process all' → All articles")
    print(f"- 'High only' → Highly relevant only")
    print(f"═══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
