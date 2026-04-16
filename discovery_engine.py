"""Discovery Engine: Finds articles from all sources - SIMPLIFIED VERSION"""

import os
from datetime import datetime

class ResearchDiscoveryEngine:
    """Discovers articles from multiple sources"""
    
    def __init__(self):
        self.articles = []
    
    def discover_articles(self):
        """Discover articles from all sources"""
        articles = []
        
        # For now, return mock articles so we can test the workflow
        # Once we verify it works, we'll add real RSS feeds
        
        mock_articles = [
            {
                'title': 'JAK inhibitors in RA-ILD: A randomized controlled trial',
                'journal': 'JAMA Rheumatology',
                'link': 'https://doi.org/10.1001/jama.2026.01234',
                'doi': 'https://doi.org/10.1001/jama.2026.01234',
                'source': 'Test Article',
                'type': 'RCT',
                'date': '2026-04-12',
            },
            {
                'title': 'Case Records of the Massachusetts General Hospital — A 62-year-old woman with progressive dyspnea',
                'journal': 'NEJM',
                'link': 'https://doi.org/10.1056/NEJMcpc2026.01234',
                'doi': 'https://doi.org/10.1056/NEJMcpc2026.01234',
                'source': 'Test Article',
                'type': 'CPC Case',
                'date': '2026-04-12',
            },
            {
                'title': 'Nintedanib vs pirfenidone in progressive RA-ILD: 24-month outcomes',
                'journal': 'Chest',
                'link': 'https://doi.org/10.1016/j.chest.2026.03.042',
                'doi': 'https://doi.org/10.1016/j.chest.2026.03.042',
                'source': 'Test Article',
                'type': 'RCT',
                'date': '2026-04-10',
            },
        ]
        
        articles.extend(mock_articles)
        return articles
    
    def format_for_curation(self, articles):
        """Format articles for Claude presentation"""
        highly_relevant = []
        medium_relevant = []
        potentially_relevant = []
        
        keywords_high = ['ra-ild', 'rheumatoid', 'jak inhibitor', 'nintedanib', 'pirfenidone']
        keywords_medium = ['ild', 'interstitial lung', 'hemodynamic', 'ett', 'coagulopathy', 'critical care']
        
        for article in articles:
            text = (article['title']).lower()
            
            if any(kw in text for kw in keywords_high):
                highly_relevant.append(article)
            elif any(kw in text for kw in keywords_medium):
                medium_relevant.append(article)
            else:
                potentially_relevant.append(article)
        
        return highly_relevant, medium_relevant, potentially_relevant
