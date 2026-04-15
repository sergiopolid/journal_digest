"""
Curation Interface: Presents articles to user in Claude for selection
"""

from anthropic import Anthropic

class CurationInterface:
    """Manages article presentation and curation"""
    
    def __init__(self, discovery_engine):
        self.engine = discovery_engine
        self.client = Anthropic()
        self.conversation_history = []
    
    def present_articles(self, articles):
        """Present discovered articles for curation"""
        
        # Format articles by relevance
        highly_relevant, medium_relevant, potentially_relevant = \
            self.engine.format_for_curation(articles)
        
        # Build presentation
        presentation = self._format_articles_for_display(
            highly_relevant, medium_relevant, potentially_relevant
        )
        
        return presentation
    
    def _format_articles_for_display(self, highly, medium, potentially):
        """Format articles for display"""
        
        output = f"""
═════════════════════════════════════════════════════════════════
📰 RESEARCH ARTICLE CURATION - Week of {self._get_week_dates()}
═════════════════════════════════════════════════════════════════

{len(highly) + len(medium) + len(potentially)} candidate articles discovered

HIGHLY RELEVANT ({len(highly)} articles):
{self._format_article_group(highly)}

MEDIUM RELEVANCE ({len(medium)} articles):
{self._format_article_group(medium)}

POTENTIALLY RELEVANT ({len(potentially)} articles):
{self._format_article_group(potentially)}

═════════════════════════════════════════════════════════════════

✅ WHAT TO DO:
Reply with the article numbers you want processed.
Example: "1, 2, 5, 7"

Or use shortcuts:
- "Process all" → All articles
- "High only" → Highly relevant only
- "Skip 3, 5" → All except 3 and 5
"""
        
        return output
    
    def _format_article_group(self, articles):
        """Format a group of articles"""
        if not articles:
            return "  (none)\n"
        
        output = ""
        for i, article in enumerate(articles, 1):
            output += f"""
  {i}. {article['title'][:70]}...
     📖 {article['journal']} | {article['doi'] or 'no DOI'}
     Type: {article['type']} | Date: {article['date']}
"""
        
        return output
    
    def _get_week_dates(self):
        from datetime import datetime, timedelta
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return f"{monday.strftime('%b %d')}-{sunday.strftime('%b %d, %Y')}"
