"""
Email Notification: Sends completion summaries
"""

import os

class EmailNotifier:
    """Handles email notifications"""
    
    def __init__(self):
        self.your_email = os.environ.get('YOUR_EMAIL')
    
    def send_completion_email(self, results):
        """Send email with processing summary"""
        
        subject = f"Research Pipeline: {len(results['created'])} articles processed ✓"
        
        body = f"""
Research Pipeline Processing Summary

Processed articles: {len(results['created'])}
Failed: {len(results['failed'])}

Created:
"""
        
        for item in results['created']:
            body += f"\n✓ {item['title'][:70]} ({item['journal']})"
        
        if results['failed']:
            body += "\n\nFailed to process:\n"
            for item in results['failed']:
                body += f"\n✗ {item['title'][:70]} - {item['error']}"
        
        body += f"""

New notes in Obsidian:
Literature/Clinical Pearls/

---
Next curation request: Sunday at 8 AM
"""
        
        # In real implementation, would send via Gmail API or SendGrid
        print(f"\n📧 Email notification ready:\nSubject: {subject}")
    
    def send_error_email(self, error):
        """Send error notification"""
        print(f"\n❌ Error notification:\n{error}")
