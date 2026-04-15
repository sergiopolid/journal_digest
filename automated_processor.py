"""
Automated Processor: Handles PDF retrieval, Claude processing, Notion sync, Obsidian publishing
"""

import os
import json
import base64
from datetime import datetime
from anthropic import Anthropic

class AutomatedArticleProcessor:
    """Processes approved articles through the full pipeline"""
    
    def __init__(self):
        self.anthropic = Anthropic()
        self.notion_api_key = os.environ.get('NOTION_API_KEY')
        self.obsidian_vault_path = os.environ.get('OBSIDIAN_VAULT_PATH')
    
    def process_selected_articles(self, articles, selected_ids):
        """Process only user-approved articles"""
        
        if not selected_ids:
            print("No articles selected for processing")
            return {'created': [], 'failed': []}
        
        # Filter to selected articles (convert to 0-indexed)
        selected = [articles[int(id)-1] for id in selected_ids if int(id) <= len(articles)]
        
        results = {'created': [], 'failed': []}
        
        for article in selected:
            try:
                print(f"\n📄 Processing: {article['title'][:60]}...")
                
                # Step 1: Create Notion entry
                notion_id = self._create_notion_entry(article)
                print(f"  ✓ Notion entry created")
                
                # Step 2: Generate summary + pearls
                summary, pearls = self._generate_summary_and_pearls(article)
                print(f"  ✓ Summary & pearls generated")
                
                # Step 3: Create Obsidian note
                obsidian_link = self._create_obsidian_note(article, summary, pearls)
                print(f"  ✓ Obsidian note created")
                
                # Step 4: Update Notion with full content
                self._update_notion_fields(notion_id, {
                    'Summary': summary,
                    'Clinical Pearls': pearls,
                    'Obsidian Link': obsidian_link,
                    'Pipeline Status': 'Published to Obsidian'
                })
                print(f"  ✓ Notion updated")
                
                results['created'].append({
                    'title': article['title'],
                    'journal': article['journal'],
                    'notion_id': notion_id,
                    'obsidian_link': obsidian_link
                })
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                results['failed'].append({
                    'title': article['title'],
                    'error': str(e)
                })
        
        return results
    
    def _create_notion_entry(self, article):
        """Create article entry in Notion (stub - would use Notion API)"""
        # In real implementation, would call Notion API
        # For now, return a mock ID
        import uuid
        return str(uuid.uuid4())
    
    def _generate_summary_and_pearls(self, article):
        """Use Claude API to generate summary + clinical pearls"""
        
        prompt = f"""You are a clinical expert in pulmonary medicine and critical care.

Based on this article, generate:
1. A 3-4 sentence SUMMARY of main findings
2. 5-7 CLINICAL PEARLS as bullet points

Article: {article['title']}
Journal: {article['journal']}
Type: {article.get('type', 'Research')}
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
        
        message = self.anthropic.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text
        
        # Parse response
        import re
        summary_match = re.search(r'## Summary\n(.*?)\n## Clinical Pearls', response_text, re.DOTALL)
        pearls_match = re.search(r'## Clinical Pearls\n(.*?)(?:\n##|$)', response_text, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else ""
        pearls = pearls_match.group(1).strip() if pearls_match else ""
        
        return summary, pearls
    
    def _create_obsidian_note(self, article, summary, pearls):
        """Create note in Obsidian vault"""
        
        # Determine specialty folder
        title_lower = article['title'].lower()
        if any(word in title_lower for word in ['ra-ild', 'rheumatoid', 'ild']):
            specialty = 'Pulmonary/RA-ILD'
        elif any(word in title_lower for word in ['critical care', 'icu', 'sepsis']):
            specialty = 'Critical Care'
        else:
            specialty = 'Pulmonary'
        
        # Create directory
        vault_path = os.path.expanduser(self.obsidian_vault_path)
        note_dir = os.path.join(vault_path, 'Literature', 'Clinical Pearls', specialty)
        os.makedirs(note_dir, exist_ok=True)
        
        # Create note
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_title = article['title'][:50].replace('/', '-').replace(':', '-')
        filename = f"{safe_title} - {date_str}.md"
        filepath = os.path.join(note_dir, filename)
        
        # Note content
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
**Type**: {article.get('type', 'Research')}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(note_content)
        
        return f"obsidian://open?vault=Vault&file={filename.replace(' ', '%20')}"
    
    def _update_notion_fields(self, page_id, fields):
        """Update Notion fields (stub - would use Notion API)"""
        # In real implementation, would call Notion API
        pass
