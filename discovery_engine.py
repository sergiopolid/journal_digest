"""
Discovery Engine: Finds articles from all sources
- Gmail Google Scholar alerts
- Journal RSS feeds (NEJM, Chest, AJRCCM, etc.)
"""

import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import base64

class ResearchDiscoveryEngine:
    """Discovers articles from multiple sources"""
    
    def __init__(self):
        self.articles = []
        self.target_journals = {
            'nejm': 'https://feeds.nejm.org/',
            'chest': 'https://www.chest.org/rss',
            'jama': 'https://jamanetwork.com/rss',
            'ajrccm': 'https://www.atsjournals.org/rss',
            'lancet_respiratory': 'https://www.thelancet.com/rss',
            'thorax': 'https://thorax.bmj.com/rss',
            'erj': 'https://erj.ersjournals.com/rss',
            'critical_care': 'https://ccforum.biomedcentral.com/rss',
        }
    
    def discover_articles(self):
        """Discover articles from all sources"""
        articles = []
        
        # Source 1: Gmail Scholar alerts
        scholar_articles = self._get_scholar_alerts()
        articles.extend(scholar_articles)
        
        # Source 2: Journal RSS feeds
        for journal_name, rss_url in self.target_journals.items():
            rss_articles = self._get_rss_articles(journal_name, rss_url)
            articles.extend(rss_articles)
        
        # Deduplicate by DOI/title
        unique_articles = {}
        for article in articles:
            key = article.get('doi') or article.get('title')
            if key not in unique_articles:
                unique_articles[key] = article
        
        return list(unique_articles.values())
    
    def _get_scholar_alerts(self):
        """Get articles from Gmail Google Scholar alerts"""
        articles = []
        
        try:
            # This would use Gmail API
            # For now, return empty list (you'll configure Gmail separately)
            pass
        except Exception as e:
            print(f"Warning: Could not fetch Scholar alerts: {e}")
        
        return articles
    
    def _get_rss_articles(self, journal_name, rss_url):
        """Get articles from journal RSS feed"""
        articles = []
        
        try:
            import feedparser
            
            feed = feedparser.parse(rss_url)
            
            # Get articles from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for entry in feed.entries[:20]:  # Get last 20 entries
                try:
                    published = datetime(*entry.published_parsed[:6])
                    if published < cutoff_date:
                        continue
                    
                    # Extract DOI if available
                    doi = None
                    if hasattr(entry, 'link'):
                        if 'doi.org' in entry.link:
                            doi = entry.link
                        elif 'doi:' in entry.summary:
                            import re
                            match = re.search(r'doi:?\s*(10\.\S+)', entry.summary)
                            if match:
                                doi = f"https://doi.org/{match.group(1)}"
                    
                    article = {
                        'title': entry.title,
                        'journal': journal_name.replace('_', ' ').title(),
                        'link': entry.link,
                        'doi': doi,
                        'source': f'Journal Website ({journal_name})',
                        'type': self._classify_article(entry.title),
                        'date': published.strftime('%Y-%m-%d'),
                        'summary': getattr(entry, 'summary', '')[:200]
                    }
                    articles.append(article)
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"Warning: Could not fetch {journal_name} RSS: {e}")
        
        return articles
    
    def _classify_article(self, title):
        """Classify article by title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['randomized', 'rct', 'trial']):
            return 'RCT'
        elif any(word in title_lower for word in ['case', 'report']):
            return 'Case Report'
        elif any(word in title_lower for word in ['review', 'meta-analysis']):
            return 'Review'
        else:
            return 'Research'
    
    def format_for_curation(self, articles):
        """Format articles for Claude presentation"""
        
        # Separate by relevance
        highly_relevant = []
        medium_relevant = []
        potentially_relevant = []
        
        keywords_high = ['ra-ild', 'rheumatoid', 'jak inhibitor', 'nintedanib', 'pirfenidone']
        keywords_medium = ['ild', 'interstitial lung', 'hemodynamic', 'ett', 'coagulopathy', 'critical care']
        
        for article in articles:
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            if any(kw in text for kw in keywords_high):
                highly_relevant.append(article)
            elif any(kw in text for kw in keywords_medium):
                medium_relevant.append(article)
            else:
                potentially_relevant.append(article)
        
        return highly_relevant, medium_relevant, potentially_relevant
