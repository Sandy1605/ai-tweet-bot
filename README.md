# 🤖 AI Tweet Bot — Automated X/Twitter Posting with Ollama

> Automatically generate and post 3 AI-written tweets daily to X/Twitter using a locally-running open-source LLM (Ollama). No paid API. No cloud. Runs on your own machine.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-green)
![Twitter API](https://img.shields.io/badge/X_API-Free_Tier-black?logo=x)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Automation](https://img.shields.io/badge/Automation-Cron_Job-orange)

---

## 📌 What This Project Does

This project automates your X/Twitter presence by:

1. **Generating tweets** using a local AI model via [Ollama](https://ollama.com) — no OpenAI API key needed
2. **Posting automatically** 3 times per day (9am, 1pm, 7pm) using cron
3. **Logging** every posted tweet with timestamp and tweet ID
4. **Rotating tweet styles** — tips, hot takes, motivational, how-to, facts, etc.

**Use case:** Grow a niche Twitter account for monetization (affiliate marketing, X revenue share, digital products) with zero manual effort.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Cron Job      │────▶│  tweet_bot.py    │────▶│  X/Twitter API  │
│ 9am, 1pm, 7pm   │     │  (Python)        │     │  (Tweepy)       │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Ollama (Local)  │
                         │  llama3/mistral  │
                         │  localhost:11434 │
                         └──────────────────┘
```

---

## ✅ Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com) installed and running
- A model pulled: `ollama pull llama3` (or mistral, phi3, gemma)
- X/Twitter Developer account (free) with Read & Write permissions

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ai-tweet-bot.git
cd ai-tweet-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your Twitter API keys
```

### 4. Start Ollama
```bash
ollama serve
ollama pull llama3
```

### 5. Test (dry run — no actual posting)
```bash
python src/tweet_bot.py --dry-run
```

### 6. Go live
```bash
python src/tweet_bot.py
```

### 7. Automate with cron
```bash
bash setup.sh
```

---

## ⚙️ Configuration

Edit `src/tweet_bot.py` → `CONFIG` section:

```python
CONFIG = {
    "niche": "tech tips, AI tools, productivity hacks",  # ← Your topic
    "ollama": {
        "model": "llama3",   # ← Your installed model
    },
    "hashtags": ["#TechTips", "#AI", "#Productivity"],   # ← Your hashtags
    "tweet_styles": [
        "educational tip",
        "hot take",
        "surprising fact",
        # add more styles...
    ]
}
```

---

## 📁 Project Structure

```
ai-tweet-bot/
├── src/
│   └── tweet_bot.py       # Main bot script
├── docs/
│   └── setup-guide.md     # Detailed setup walkthrough
├── examples/
│   └── sample_tweets.md   # Example AI-generated tweets
├── .env.example            # Template for API keys
├── requirements.txt        # Python dependencies
├── setup.sh               # Cron job installer
└── README.md
```

---

## 🐦 Example Generated Tweets

> "Stop using Google for everything. These 5 AI tools will save you 3 hours daily: [thread] #TechTips #AI"

> "Unpopular opinion: Most developers waste 40% of their day on tasks that could be automated in an afternoon. Here's how to start: #Productivity"

> "You don't need a fancy setup to build AI apps. Ollama runs GPT-level models free on your laptop. Here's the 5-minute setup: #Developer"

---

## 💰 Monetization Strategy

| Method | How |
|---|---|
| X Revenue Share | Grow to 500 followers + 5M impressions → apply |
| Affiliate Marketing | Add links in bio, tweet content that drives clicks |
| Digital Products | Sell templates/guides on Gumroad, promote in tweets |
| Sponsored Tweets | Brands pay per tweet once you have an audience |

---

## 📊 Limits & Costs

| Item | Cost |
|---|---|
| Ollama (tweet generation) | **Free** — runs locally |
| X API Free Tier (posting) | **Free** — 1,500 tweets/month |
| This bot uses | ~90 tweets/month |
| Server/hosting needed | **None** — runs on your PC |

---

## 🛠️ Tech Stack

- **Python 3** — main language
- **Ollama** — local LLM inference
- **Tweepy** — Twitter/X API wrapper
- **Cron** — scheduling
- **llama3 / mistral / phi3** — open source LLMs

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙋 Author

Built by [@WealthWellnessN](https://x.com/WealthWellnessN)  
*Showcasing AI automation for social media growth*
