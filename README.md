# Research Pipeline - Automated Article Discovery

Automatically discover, curate, and process research articles weekly.

## Features

- 📰 Discovers 15-25 articles weekly from 9 target journals + Gmail Scholar alerts
- 👁️ Presents articles to you for curation in Claude
- ⚙️ Automatically processes selected articles:
  - Retrieves PDFs
  - Generates summaries & clinical pearls with Claude API
  - Creates Notion entries
  - Publishes to Obsidian vault
- 📧 Email notifications with completion summaries

## Setup

See SETUP.md for detailed instructions.

### Quick Start

1. Fork this repository
2. Add secrets in GitHub Settings
3. Enable Actions
4. Done! Runs every Sunday at 8 AM

## Workflow

**Sunday 8 AM**: Pipeline discovers articles  
**Sunday afternoon**: You review and select articles  
**Monday-Friday**: Automation processes articles  
**Friday evening**: Email notification with results

Your time: ~5 minutes per week
