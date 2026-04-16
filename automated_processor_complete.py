#!/usr/bin/env python3
"""
Automated Processor: Handles selected articles
- Creates Notion entries
- Generates summaries with Claude
- Creates Obsidian notes
- Updates Notion status
"""

import os
from datetime import datetime
from anthropic import Anthropic
import requests
import re

# Configuration
notion_api_key = os.environ.get('NOTION_API_KEY')
notion_db_id = "34482b8a2d8f8040b027c1c0b0202a68"
obsidian_vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '/Users/sergiopoli/Documents/Obsidian Vault/')
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

# Initialize clients
anthropic_client = Anthropic(api_key=anthropic_key)


class NotionIntegration:
    """Notion database operations"""
    
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
            return None
        except Exception as e:
            print(f"  Error creating Notion entry: {e}")
            return None
    
    def update_entry(self, notion_id, summary, pearls, obsidian_link):
        """Update Notion entry with full content"""
        try:
            data = {
                "properties": {
                    "Summary": {
                        "rich_text": [{"text": {"content": summary[:2000]}}]
                    },
                    "Clinical Pearls": {
                        "rich_text": [{"text": {"content": pearls[:2000]}}]
                    },
                    "Obsidian Link": {
                        "url": obsidian_link
                    },
                    "Pipeline Status": {
                        "select": {"name": "Published to Obsidian"}
                    },
                    "Date Processed": {
                        "date": {"start": datetime.now().strftime('%Y-%m-%d')}
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
            print(f"  Error updating Notion entry: {e}")
            return False


class ClaudeSummaryGenerator:
    """Generate summaries and clinical pearls"""
    
    def generate(self, article):
        """Generate summary and pearls using Claude"""
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
            print(f"  Error generating summary: {e}")
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
            
            return filename
        except Exception as e:
            print(f"  Error creating Obsidian note: {e}")
            return None


def process_articles(articles, selected_indices):
    """Process selected articles through full pipeline"""
    
    if not selected_indices:
        print("❌ No articles selected")
        return
    
    # Filter to selected articles
    selected = [articles[i-1] for i in selected_indices if i <= len(articles)]
    
    notion = NotionIntegration()
    claude = ClaudeSummaryGenerator()
    obsidian = ObsidianPublisher()
    
    results = {'created': [], 'failed': []}
    
    print(f"\n⚙️  PROCESSING {len(selected)} SELECTED ARTICLES")
    print("=" * 70)
    
    for article in selected:
        print(f"\n📄 {article['title'][:60]}...")
        
        # Step 1: Create Notion entry
        notion_id = notion.create_entry(article)
        if notion_id:
            print(f"  ✓ Notion entry created")
        else:
            print(f"  ✗ Notion entry failed")
            results['failed'].append(article['title'])
            continue
        
        # Step 2: Generate summary and pearls
        summary, pearls = claude.generate(article)
        if summary:
            print(f"  ✓ Summary generated")
        else:
            print(f"  ✗ Summary generation failed")
            results['failed'].append(article['title'])
            continue
        
        # Step 3: Create Obsidian note
        obsidian_file = obsidian.publish(article, summary, pearls)
        if obsidian_file:
            print(f"  ✓ Obsidian note created: {obsidian_file}")
        else:
            print(f"  ✗ Obsidian note failed")
            results['failed'].append(article['title'])
            continue
        
        # Step 4: Update Notion with full content
        obsidian_link = f"obsidian://open?vault=Vault&file={obsidian_file.replace(' ', '%20')}"
        notion.update_entry(notion_id, summary, pearls, obsidian_link)
        print(f"  ✓ Notion updated with content")
        
        results['created'].append({
            'title': article['title'],
            'journal': article['journal'],
            'obsidian_file': obsidian_file
        })
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ PROCESSING COMPLETE")
    print(f"   Processed: {len(results['created'])}")
    print(f"   Failed: {len(results['failed'])}")
    
    if results['created']:
        print(f"\n📝 New Obsidian notes created:")
        for item in results['created']:
            print(f"   • {item['title'][:70]}")
    
    if results['failed']:
        print(f"\n❌ Failed:")
        for item in results['failed']:
            print(f"   • {item}")
    
    return results
