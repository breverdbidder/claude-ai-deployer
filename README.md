# Claude AI Auto-Deploy System

**Automatically detect, encode, and deploy artifacts from Claude AI to GitHub**

🕐 **Created:** January 3, 2025  
👤 **Author:** Ariel Shapira / BidDeed.AI  
📦 **Version:** 1.0.0

---

## The Problem This Solves

**Before:** Claude AI creates files in `/mnt/user-data/outputs/` → Files lost when chat ends → Manual copy/paste to GitHub → Wasted work

**After:** Claude AI creates files → Auto-detected → Auto-deployed to GitHub → Zero manual intervention

---

## How It Works

```
┌─────────────────────────────────────────────┐
│  1. Claude AI creates file in chat          │
│  2. Deployer scans outputs directory        │
│  3. Smart router determines target repo     │
│  4. File encoded (Base64 if binary)         │
│  5. Manifest created with metadata          │
│  6. Pushed to GitHub via REST API           │
│  7. Verification confirms deployment        │
│  8. Logged to Supabase insights table       │
└─────────────────────────────────────────────┘
```

---

## Features

### ✅ Smart File Routing
Automatically routes files to correct repos based on patterns:

| File Pattern | Target Repo | Target Path |
|-------------|-------------|-------------|
| `*.yml` | life-os | `.github/workflows/` |
| `*_node*.py` | life-os | `src/nodes/` |
| `*_agent*.py` | life-os | `src/agents/` |
| `*_scraper*.py` | brevard-bidder-scraper | `src/scrapers/` |
| `*.py` | life-os | `src/` |
| `*.html`, `*.css`, `*.js` | biddeed-conversational-ai | `public/` |
| `*.md` | life-os | `docs/` |
| `*.docx`, `*.pdf` | life-os | `reports/` |
| `SKILL.md` | life-os | `skills/` |

### ✅ Binary & Text Support
- Text files: UTF-8 encoding
- Binary files: Base64 encoding
- Auto-detection based on content

### ✅ Deployment Verification
- SHA256 checksums
- GitHub API verification
- Retry logic (3 attempts)
- Detailed error reporting

### ✅ Audit Trail
- JSON deployment logs
- Supabase insights logging
- GitHub commit history
- Artifact retention (30 days)

---

## Quick Start

### 1. GitHub Repository Setup

```bash
# Create new repo on GitHub
gh repo create breverdbidder/claude-ai-deployer --public

# Push initial code
git init
git add .
git commit -m "Initial commit: Claude AI Auto-Deploy System v1.0.0"
git branch -M main
git remote add origin https://github.com/breverdbidder/claude-ai-deployer.git
git push -u origin main
```

### 2. Configure GitHub Secrets

Add to repository settings → Secrets and variables → Actions:

```
GITHUB_TOKEN: ghp_YOUR_TOKEN_HERE
SUPABASE_KEY: [your-supabase-key]
```

### 3. Enable GitHub Actions

The workflow runs automatically:
- **Scheduled:** Every 5 minutes
- **Manual:** Via workflow_dispatch

### 4. Test Deployment

```bash
# Run locally
python claude_ai_deployer.py

# Verify deployments
python deployment_verifier.py
```

---

## Usage

### Automatic Mode (Recommended)

1. Claude AI creates files in `/mnt/user-data/outputs/`
2. GitHub Action runs every 5 minutes
3. New files auto-deployed to appropriate repos
4. Verification confirms success
5. Results logged to Supabase

### Manual Mode

```bash
# Deploy all files in outputs
python claude_ai_deployer.py

# Execute generated deployment commands
bash deploy_commands.sh

# Verify all deployments
python deployment_verifier.py
```

---

## File Structure

```
claude-ai-deployer/
├── claude_ai_deployer.py      # Main deployment orchestrator
├── deployment_verifier.py      # Verification script
├── claude_ai_auto_deploy.yml   # GitHub Actions workflow
├── README.md                   # This file
├── deployment_log.json         # Generated log
├── deploy_commands.sh          # Generated commands
└── verification_report.json    # Generated verification
```

---

## Deployment Routing Rules

The system uses regex patterns to route files:

```python
ROUTING_RULES = {
    r'.*\.yml$': {
        'repo': 'life-os',
        'path': '.github/workflows/',
        'description': 'GitHub Actions workflow'
    },
    r'.*_node.*\.py$': {
        'repo': 'life-os',
        'path': 'src/nodes/',
        'description': 'LangGraph node module'
    },
    # ... see claude_ai_deployer.py for full list
}
```

To add new routing rules, edit `ROUTING_RULES` dictionary.

---

## Configuration

### Environment Variables

```bash
# Required
GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE
SUPABASE_URL=https://mocerqjnksmhcjzxrewo.supabase.co
SUPABASE_KEY=[your-key]

# Optional
OUTPUTS_DIR=/mnt/user-data/outputs  # Default
GITHUB_USER=breverdbidder           # Default
```

### Workflow Schedule

Edit `.github/workflows/claude_ai_auto_deploy.yml`:

```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes (default)
  # - cron: '*/15 * * * *'  # Every 15 minutes
  # - cron: '0 * * * *'     # Every hour
```

---

## Deployment Process

### 1. File Detection

```python
deployer = ClaudeAIDeployer()
files = deployer.scan_outputs()  # Scans /mnt/user-data/outputs
```

### 2. Smart Routing

```python
route = deployer.route_file(filepath)
# Returns: {'repo': 'life-os', 'path': 'src/', ...}
```

### 3. Content Encoding

```python
content, is_binary = deployer.encode_file(filepath)
# Text files: UTF-8 string
# Binary files: Base64 encoded string
```

### 4. Manifest Creation

```python
manifest = deployer.create_deployment_manifest(filepath, route, content, is_binary)
# Includes: checksum, size, timestamp, metadata
```

### 5. GitHub Push

```python
result = deployer.push_to_github(manifest, content)
# Uses GitHub REST API to create/update file
```

### 6. Verification

```python
verifier = DeploymentVerifier(log_path)
results = verifier.verify_all()
# Confirms files exist in GitHub
```

---

## Example Deployment Log

```json
{
  "version": "1.0.0",
  "timestamp": "2025-01-03T23:52:00Z",
  "total_deployments": 3,
  "deployments": [
    {
      "filepath": "/mnt/user-data/outputs/new_workflow.yml",
      "manifest": {
        "filename": "new_workflow.yml",
        "target_repo": "life-os",
        "target_path": ".github/workflows/new_workflow.yml",
        "checksum": "a3f8b9c2...",
        "size_bytes": 1250
      },
      "result": {
        "status": "prepared",
        "repo": "life-os",
        "path": ".github/workflows/new_workflow.yml"
      },
      "timestamp": "2025-01-03T23:52:15Z"
    }
  ]
}
```

---

## Verification Report

```json
{
  "timestamp": "2025-01-03T23:52:00Z",
  "verification_results": {
    "total": 3,
    "verified": 3,
    "failed": 0,
    "success_rate": 1.0,
    "details": [
      {
        "filename": "new_workflow.yml",
        "repo": "life-os",
        "path": ".github/workflows/new_workflow.yml",
        "verified": true
      }
    ]
  }
}
```

---

## Supabase Integration

Deployment results logged to `insights` table:

```sql
INSERT INTO insights (timestamp, category, metric_name, metric_value, details)
VALUES (
  '2025-01-03T23:52:00Z',
  'deployment',
  'claude_ai_auto_deploy',
  3,  -- Number of files deployed
  '{"total_deployments": 3, "deployments": [...]}'
);
```

---

## Troubleshooting

### Files Not Deploying

1. Check outputs directory exists: `/mnt/user-data/outputs`
2. Verify GitHub token has correct permissions
3. Check workflow run logs in GitHub Actions
4. Review `deployment_log.json` for errors

### Verification Failures

1. Wait 30 seconds after deployment for GitHub propagation
2. Check GitHub API rate limits
3. Verify file paths match routing rules
4. Review `verification_report.json` for details

### Routing Issues

1. Add custom routing rule to `ROUTING_RULES`
2. Test pattern matching with `re.match(pattern, filename)`
3. Check default fallback route (artifacts/)

---

## Architecture Decisions

### Why REST API (not Git CLI)?

- Works in GitHub Actions without checkout
- Atomic file operations
- Built-in conflict detection
- Easier error handling
- No local Git state management

### Why Every 5 Minutes?

- Balance between responsiveness and API rate limits
- GitHub API: 5,000 requests/hour = ~83/minute = 16 per 5-min window
- Deployments typically < 10 files = safe margin

### Why Base64 for Binary?

- GitHub API requires Base64 for binary content
- Consistent encoding across file types
- Built-in content integrity

### Why Separate Verification?

- GitHub propagation delay (5-30 seconds)
- Explicit success confirmation
- Audit trail for compliance
- Debugging deployment issues

---

## Future Enhancements

### Planned Features

- [ ] Slack/email notifications
- [ ] Rollback capability
- [ ] Conflict resolution strategies
- [ ] Multi-branch support
- [ ] Cloudflare Pages auto-trigger
- [ ] Real-time websocket monitoring
- [ ] Deployment preview/approval workflow
- [ ] Integration with Claude Code

### Not Planned

- Local file watching (runs in GitHub Actions)
- GUI interface (CLI/automation focused)
- Multi-cloud deployment (GitHub-only)

---

## Cost Analysis

### Time Savings

**Before Claude AI Auto-Deploy:**
- Manual copy/paste: 2-5 min per file
- Git commit/push: 1-2 min
- Verification: 1 min
- **Total:** 4-8 min per deployment

**After Claude AI Auto-Deploy:**
- Zero manual intervention
- **Total:** 0 min per deployment

**ROI:** 100% time recovery on deployments

### API Costs

- GitHub Actions: Free (2,000 min/month on Free tier)
- GitHub API: Free (5,000 requests/hour)
- Supabase: Free tier sufficient
- **Total:** $0/month

---

## Integration with BidDeed.AI Stack

This tool complements the BidDeed.AI agentic ecosystem:

| Component | Role |
|-----------|------|
| **Claude AI** | AI Architect - Creates code/docs |
| **Claude Code** | Agentic Engineer - 7-hour dev sessions |
| **LangGraph** | Orchestration - Multi-agent workflows |
| **GitHub Actions** | Runtime - Executes workflows |
| **Supabase** | Database - State persistence |
| **Claude AI Deployer** | **Auto-deployment - Zero manual intervention** |

---

## License

MIT License - Copyright (c) 2025 Ariel Shapira / BidDeed.AI

---

## Support

For issues or questions:
1. Check `deployment_log.json` and `verification_report.json`
2. Review GitHub Actions workflow logs
3. Search Supabase insights table for deployment records
4. Create GitHub issue with logs attached

---

## Credits

**Created by:** Ariel Shapira  
**Company:** BidDeed.AI / Everest Capital USA  
**Purpose:** Eliminate manual deployment friction from Claude AI workflows  
**Date:** January 3, 2025

**Autonomous execution. Zero human-in-the-loop. 100% deployment automation.**
