#!/usr/bin/env python3
"""
Automated Research Pipeline Orchestrator
Discovers articles, presents for curation, processes selections
"""

import os
import json
from datetime import datetime, timedelta
from anthropic import Anthropic

# Import local modules
from discovery_engine import ResearchDiscoveryEngine
from curation_interface import CurationInterface
from automated_processor import AutomatedArticleProcessor
from email_notification import EmailNotifier

def main():
    """Main orchestration function"""
    
    print("=" * 70)
    print("🚀 RESEARCH PIPELINE: ARTICLE DISCOVERY & CURATION")
    print("=" * 70)
    
    try:
        # Step 1: Discover articles
        print("\n📰 STEP 1: Discovering articles from all sources...")
        discovery = ResearchDiscoveryEngine()
        articles = discovery.discover_articles()
        
        if not articles:
            print("❌ No articles discovered this week")
            return
        
        print(f"✅ Found {len(articles)} candidate articles")
        
        # Step 2: Present for curation
        print("\n👁️  STEP 2: Presenting articles for curation...")
        curation = CurationInterface(discovery)
        presentation = curation.present_articles(articles)
        
        print("\n" + "=" * 70)
        print("CURATION REQUEST SENT TO CLAUDE")
        print("=" * 70)
        print("\nWaiting for your selections...\n")
        print(presentation)
        
        # Note: In GitHub Actions, we'd handle this via Claude's response
        # For now, log that we're waiting for user input
        
        print("\n✅ Please respond in Claude with your selections")
        print("   Example: '1, 2, 5, 7'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error notification
        try:
            notifier = EmailNotifier()
            notifier.send_error_email(str(e))
        except:
            pass

if __name__ == "__main__":
    main()
