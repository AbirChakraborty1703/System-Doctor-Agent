# Automatic GitHub Sync Guide for SystemDoctor AI

## Overview

This guide explains different methods to automatically fetch and sync updates from your GitHub repository.

## Method 1: Git Pull on Startup (Local Machine)

Automatically pull latest changes when you start development:

```bash
#!/bin/bash
# save as: sync_and_start.sh

cd "d:/System Doctor"
git pull origin main

# Start Streamlit app
streamlit run app.py
```

**Run it:**
```bash
bash sync_and_start.sh
```

## Method 2: GitHub Actions - Auto-Deployment

Create a workflow that automatically deploys when you push to main:

**File:** `.github/workflows/deploy.yml`

```yaml
name: Auto Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Streamlit Cloud
        run: |
          # Streamlit Cloud automatically deploys on push
          echo "Deployment triggered automatically"
```

## Method 3: Webhook for Real-Time Updates

Set up GitHub webhook to trigger updates on your server:

**Python Webhook Receiver:**

```python
# save as: webhook_receiver.py

from flask import Flask, request
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)
GITHUB_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')

def verify_github_signature(payload_body, signature_header):
    """Verify GitHub webhook signature"""
    if not signature_header:
        return False
    
    signature = hmac.new(
        GITHUB_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, signature_header.split('=')[1])

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    """Handle GitHub push events"""
    signature = request.headers.get('X-Hub-Signature-256')
    payload = request.get_data()
    
    if not verify_github_signature(payload, signature):
        return {'status': 'unauthorized'}, 401
    
    event = request.headers.get('X-GitHub-Event')
    
    if event == 'push':
        # Pull latest changes
        subprocess.run(['git', 'pull', 'origin', 'main'], 
                      cwd='/path/to/System Doctor',
                      capture_output=True)
        
        # Restart services
        subprocess.run(['docker-compose', 'restart'],
                      cwd='/path/to/System Doctor',
                      capture_output=True)
        
        return {'status': 'updated'}, 200
    
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Setup:**
1. Set environment variable: `GITHUB_WEBHOOK_SECRET=your_secret_key`
2. Go to GitHub repo → Settings → Webhooks
3. Add webhook with URL: `https://your-server.com/webhook/github`
4. Select "Push events"
5. Add secret: `your_secret_key`

## Method 4: Scheduled Git Sync (Cron Job)

Automatically pull changes at regular intervals:

**Linux/Mac - Add to crontab:**

```bash
crontab -e

# Pull every hour
0 * * * * cd /path/to/System\ Doctor && git pull origin main

# Pull every 30 minutes
*/30 * * * * cd /path/to/System\ Doctor && git pull origin main

# Pull every day at 2 AM
0 2 * * * cd /path/to/System\ Doctor && git pull origin main
```

**Windows - Task Scheduler:**

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Set schedule (hourly, daily, etc.)
4. Action: Start program
   - Program: `git.exe`
   - Arguments: `-C "d:\System Doctor" pull origin main`

## Method 5: Streamlit Cloud Auto-Deployment

Streamlit Cloud automatically deploys when you push to your connected GitHub repo:

**Setup:**
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repository
4. Select branch: `main`
5. Select file: `app.py`
6. Click Deploy

**Auto-updates happen when:**
- You push to the `main` branch
- Changes are detected within 1-2 minutes
- Deployment is automatic (no manual action needed)

## Method 6: Git Fetch + Auto-Pull Script

Python script for continuous sync:

```python
# save as: auto_sync.py

import subprocess
import time
import os
from datetime import datetime

REPO_PATH = r"d:\System Doctor"
SYNC_INTERVAL = 300  # 5 minutes in seconds

def pull_latest():
    """Pull latest changes from GitHub"""
    try:
        os.chdir(REPO_PATH)
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[{datetime.now()}] ✓ Synced successfully")
            if result.stdout.strip() != "Already up to date.":
                print(f"  Changes: {result.stdout}")
                # Optionally restart services here
        else:
            print(f"[{datetime.now()}] ✗ Sync failed: {result.stderr}")
    
    except Exception as e:
        print(f"[{datetime.now()}] ✗ Error: {e}")

def start_auto_sync():
    """Start continuous sync loop"""
    print("Starting automatic GitHub sync...")
    print(f"Sync interval: {SYNC_INTERVAL} seconds")
    
    while True:
        try:
            pull_latest()
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            print("\nSync stopped by user")
            break

if __name__ == "__main__":
    start_auto_sync()
```

**Run it:**
```bash
python auto_sync.py
```

## Method 7: Docker Compose with Auto-Restart

Update docker-compose to auto-pull and restart:

```yaml
version: '3.9'

services:
  git-sync:
    image: alpine/git
    volumes:
      - .:/repo
    working_dir: /repo
    command: >
      sh -c "while true; do
        git pull origin main;
        sleep 300;
      done"
    restart: always

  streamlit:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.streamlit
    ports:
      - "8501:8501"
    depends_on:
      - git-sync
    restart: always

  api:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.api
    ports:
      - "8000:8000"
    depends_on:
      - git-sync
    restart: always
```

## Recommended Setup

**For Development:**
Use Method 1 (Git Pull on Startup) + Manual push

**For Staging:**
Use Method 4 (Cron Job) every 30 minutes

**For Production:**
Use Method 5 (Streamlit Cloud Auto-Deploy) - most reliable

**For Self-Hosted:**
Use Method 3 (Webhook) or Method 6 (Auto-Sync Script)

## Monitoring Auto-Sync

**Check sync logs:**
```bash
# View git pull history
git reflog

# Check last fetch time
git log -1 --format="%ai" origin/main
```

## Troubleshooting

**Issue:** "fatal: not a git repository"
```bash
# Solution: Ensure you're in correct directory
cd "d:/System Doctor"
git status
```

**Issue:** "Permission denied" on cron job
```bash
# Solution: Use full paths and ensure permissions
chmod +x /path/to/sync_script.sh
```

**Issue:** "Merge conflicts" on auto-pull
```bash
# Solution: Configure auto-stash or use pull strategy
git config pull.ff only  # Fast-forward only (no merge conflicts)
```

## Best Practices

1. ✅ Always use `git pull origin main` (not just `git pull`)
2. ✅ Set up proper error handling and logging
3. ✅ Monitor sync status regularly
4. ✅ Use webhooks for production environments
5. ✅ Keep `.env` files out of repo (use .gitignore)
6. ✅ Test auto-sync with dummy changes first
7. ✅ Set up alerts for failed syncs

---

**Last Updated:** 2025-01-01
