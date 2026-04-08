# Complete Setup Guide (Beginner Friendly)

## PART 1 - Install Tools

### Python
1. Go to https://www.python.org/downloads/
2. Download Python 3.11+
3. IMPORTANT: Check "Add Python to PATH" during install
4. Click Install

### VS Code
1. Go to https://code.visualstudio.com/
2. Download and install

### Ollama (local AI)
1. Go to https://ollama.com
2. Download and install
3. Open terminal, run: ollama pull llama3
   (downloads the AI model, about 4GB)

---

## PART 2 - Configure Project

### Create your .env file
In VS Code, find .env.example on the left panel.
Right-click it, copy, paste, rename to just: .env
Open .env and paste your Twitter keys:

TWITTER_API_KEY=paste_consumer_key_here
TWITTER_API_SECRET=paste_consumer_secret_here
TWITTER_ACCESS_TOKEN=paste_access_token_here
TWITTER_ACCESS_SECRET=paste_access_token_secret_here
TWITTER_BEARER_TOKEN=paste_bearer_token_here

No spaces, no quotes.

### Install Python packages
Press Ctrl+backtick in VS Code to open terminal, then run:
pip install tweepy requests

---

## PART 3 - Test the Bot

Step 1: Start Ollama
Open a terminal window and run: ollama serve
Keep this window open the whole time!

Step 2: Safe test (does NOT post anything)
python src/tweet_bot.py --dry-run

If you see a tweet printed on screen, everything works!

Step 3: Post a real tweet
python src/tweet_bot.py

Check your Twitter - the tweet should appear!

---

## PART 4 - Automate (Windows)

1. Right-click setup_windows_scheduler.bat
2. Click "Run as Administrator"
3. Done! Bot will post at 9am, 1pm, 7pm every day

To check: Search "Task Scheduler" in Windows, look for "AI Tweet Bot"

NOTE: Your PC must be ON and ollama serve must be running!

---

## PART 5 - Put on GitHub

### Install Git
1. Go to https://git-scm.com/downloads
2. Download and install (keep all default settings)

### One-time setup
Open VS Code terminal and run:
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

### Create GitHub repo
1. Go to https://github.com and sign up (free)
2. Click + button top right, then "New repository"
3. Name: ai-tweet-bot
4. Set to Public
5. Do NOT check "Add README"
6. Click "Create repository"
7. Copy the URL shown (https://github.com/YOURNAME/ai-tweet-bot.git)

### Upload your code
Run these in VS Code terminal one by one:

git init
git add .
git commit -m "Initial commit: AI tweet bot with Ollama"
git branch -M main
git remote add origin https://github.com/YOURNAME/ai-tweet-bot.git
git push -u origin main

It will ask for GitHub username + password.
For password, use a Personal Access Token:
GitHub.com > Settings > Developer Settings > Personal Access Tokens > Generate new token

---

## Troubleshooting

"python is not recognized"
= Reinstall Python, check the "Add to PATH" box

"Cannot connect to Ollama"
= Open terminal and run: ollama serve  (keep it open)

"401 Unauthorized"  
= Wrong API keys in .env - check each one carefully

"403 Forbidden"
= Access Token is read-only
= Go to developer.twitter.com, regenerate token with Read+Write

"ModuleNotFoundError: No module named tweepy"
= Run: pip install tweepy requests
