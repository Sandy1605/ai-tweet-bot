import sys
import os
import json
import random
import requests
import tweepy
import argparse
from datetime import datetime
from pathlib import Path

# Load .env (for local testing only)
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

CONFIG = {
    "twitter": {
        "api_key":             os.getenv("TWITTER_API_KEY", ""),
        "api_secret":          os.getenv("TWITTER_API_SECRET", ""),
        "access_token":        os.getenv("TWITTER_ACCESS_TOKEN", ""),
        "access_token_secret": os.getenv("TWITTER_ACCESS_SECRET", ""),
        "bearer_token":        os.getenv("TWITTER_BEARER_TOKEN", ""),
    },
    "groq": {
        "url":   "https://api.groq.com/openai/v1/chat/completions",
        "key":   os.getenv("GROQ_API_KEY", ""),
        "model": "llama-3.1-8b-instant",
    },
    "feeds": [
        ("https://news.google.com/rss/search?q=stock+market+investing+today&hl=en&gl=US&ceid=US:en", "finance"),
        ("https://news.google.com/rss/search?q=warren+buffett+charlie+munger&hl=en&gl=US&ceid=US:en", "finance"),
        ("https://news.google.com/rss/search?q=personal+finance+wealth+tips&hl=en&gl=US&ceid=US:en", "finance"),
        ("https://news.google.com/rss/search?q=passive+income+financial+freedom&hl=en&gl=US&ceid=US:en", "finance"),
        ("https://news.google.com/rss/search?q=fitness+workout+exercise+tips&hl=en&gl=US&ceid=US:en", "fitness"),
        ("https://news.google.com/rss/search?q=health+longevity+research+2026&hl=en&gl=US&ceid=US:en", "fitness"),
        ("https://news.google.com/rss/search?q=nutrition+diet+healthy+eating&hl=en&gl=US&ceid=US:en", "fitness"),
        ("https://news.google.com/rss/search?q=mental+health+wellness+habits&hl=en&gl=US&ceid=US:en", "fitness"),
        ("https://news.google.com/rss/search?q=nordic+lifestyle+wellness+health&hl=en&gl=US&ceid=US:en", "fitness"),
    ],
    "keywords": {
        "finance": [
            "stock", "market", "invest", "nasdaq", "bitcoin", "crypto",
            "inflation", "fed", "recession", "economy", "earnings",
            "buffett", "munger", "lynch", "dalio", "wealth", "millionaire",
            "passive income", "financial freedom", "portfolio", "dividend",
            "etf", "net worth",
        ],
        "fitness": [
            "fitness", "workout", "exercise", "health", "longevity", "diet",
            "nutrition", "mental health", "sleep", "weight", "running", "gym",
            "muscle", "protein", "study", "research", "supplement", "wellness",
            "habit", "mindset", "stress", "anxiety", "recovery", "nordic",
            "meditation", "calories", "training",
        ],
    },
    "personas": {
        "finance": [
            {"name": "Warren Buffett", "signature": "- Warren Buffett",
             "style": "wise, long-term value investing, patient, simple folksy Omaha wisdom"},
            {"name": "Charlie Munger", "signature": "- Charlie Munger",
             "style": "blunt, contrarian, mental models, sharp wit, no-nonsense"},
            {"name": "Peter Lynch",    "signature": "- Peter Lynch",
             "style": "practical, invest in what you know, optimistic, everyday examples"},
        ],
        "fitness": [
            {"name": "a Nordic wellness coach",       "signature": "- Nordic Wellness",
             "style": "calm, nature-inspired, connects body and wealth, balanced lifestyle"},
            {"name": "a longevity and health expert", "signature": "- Longevity Lab",
             "style": "science-based, sleep nutrition exercise for peak performance"},
            {"name": "a fitness and finance coach",   "signature": "- Fit and Wealthy",
             "style": "connects physical discipline to financial discipline, motivational"},
        ],
    },
    "hashtags": {
        "finance": [
            "#Investing", "#StockMarket", "#PersonalFinance", "#FinancialFreedom",
            "#WealthBuilding", "#PassiveIncome", "#MoneyMindset", "#FinancialLiteracy",
            "#InvestingTips", "#WealthMindset", "#StockMarketNews", "#ValueInvesting",
            "#DividendInvesting", "#RetirementPlanning", "#FinanceTwitter",
        ],
        "fitness": [
            "#FitnessMotivation", "#HealthyLiving", "#Wellness", "#WorkoutTips",
            "#MentalHealth", "#HealthyHabits", "#Longevity", "#NordicLife",
            "#MindBody", "#FitLife", "#NutritionTips", "#HealthFirst",
            "#FitnessJourney", "#HealthyMindset", "#WellnessWednesday",
        ],
        "brand": "#WealthWellness",
    },
    "log_file": "tweet_log.json",
}


def get_hashtags(category: str, count: int = 3) -> str:
    pool = CONFIG["hashtags"][category].copy()
    random.shuffle(pool)
    selected = pool[:count - 1]
    selected.append(CONFIG["hashtags"]["brand"])
    return " ".join(selected)


def get_trending_topics() -> dict:
    found = {"finance": [], "fitness": []}
    for url, category in CONFIG["feeds"]:
        try:
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            for chunk in r.text.split("<item>")[1:4]:
                t1 = chunk.find("<title>") + 7
                t2 = chunk.find("</title>")
                if t1 < 7 or t2 < 0:
                    continue
                title = chunk[t1:t2].replace(
                    "<![CDATA[", "").replace("]]>", "").strip()
                if any(kw in title.lower() for kw in CONFIG["keywords"][category]):
                    found[category].append({"title": title, "category": category})
        except Exception:
            continue

    result = {}
    for cat, items in found.items():
        seen, unique = set(), []
        for t in items:
            if t["title"] not in seen:
                seen.add(t["title"])
                unique.append(t)
        result[cat] = unique

    print(f"Finance: {len(result.get('finance',[]))} | Fitness: {len(result.get('fitness',[]))}")
    return result


def pick_balanced_trend(trends: dict) -> dict:
    log = load_log()
    recent = [e for e in log[-6:] if "category" in e]
    fin = sum(1 for e in recent if e["category"] == "finance")
    fit = sum(1 for e in recent if e["category"] == "fitness")

    if fit <= fin and trends.get("fitness"):
        cat = "fitness"
    elif trends.get("finance"):
        cat = "finance"
    else:
        cat = "fitness" if trends.get("fitness") else "finance"

    pool = trends.get(cat, [])
    if not pool:
        pool = [{"title": f"building healthy {cat} habits daily", "category": cat}]

    print(f"Category: {cat} (finance={fin} fitness={fit} in last 6)")
    return random.choice(pool[:5])


def generate_tweet(trend: dict, persona: dict) -> str:
    """Uses GROQ cloud API — free, fast, no local install needed."""
    category = trend["category"]
    hashtag_str = get_hashtags(category, 3)
    sig = persona["signature"]

    prompt = f"""You are {persona['name']} — known for {persona['style']}.

Trending topic: "{trend['title']}"

Write ONE tweet reacting to this as {persona['name']}.

Rules:
- Maximum 180 characters — strict, count carefully
- Must be a COMPLETE sentence — never end mid-word
- Sound exactly like {persona['name']}
- Be punchy, direct and shareable
- No hashtags in your output
- No signature in your output
- No AI disclaimers
- Output tweet text ONLY

Tweet:"""

    groq_key = CONFIG["groq"]["key"]
    if not groq_key:
        raise ValueError("GROQ_API_KEY not found! Add it to GitHub Secrets.")

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": CONFIG["groq"]["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.85,
    }

    print(f"  Calling Groq API ({CONFIG['groq']['model']})...")
    r = requests.post(
        CONFIG["groq"]["url"],
        headers=headers,
        json=payload,
        timeout=30
    )
    r.raise_for_status()

    text = r.json()["choices"][0]["message"]["content"].strip()
    text = text.strip('"').strip("'")
    lines = [l for l in text.split("\n") if not l.strip().startswith("#")]
    text = " ".join(lines).strip()

    # Smart trim at sentence boundary
    if len(text) > 180:
        trimmed = text[:180]
        last_end = max(trimmed.rfind('.'), trimmed.rfind('!'), trimmed.rfind('?'))
        if last_end > 80:
            text = trimmed[:last_end + 1]
        else:
            text = trimmed[:trimmed.rfind(' ')] + "."

    return f"{text}\n{sig}\n\n{hashtag_str}"


def post_tweet(text: str, dry_run: bool = False) -> dict:
    if dry_run:
        print(f"\n[DRY RUN]\n{text}\n{len(text)}/280 chars")
        return {"id": "dry_run", "text": text}

    cfg = CONFIG["twitter"]
    if not cfg["api_key"]:
        raise ValueError("Twitter API keys not found! Check GitHub Secrets.")

    client = tweepy.Client(
        bearer_token=cfg["bearer_token"],
        consumer_key=cfg["api_key"],
        consumer_secret=cfg["api_secret"],
        access_token=cfg["access_token"],
        access_token_secret=cfg["access_token_secret"],
    )
    resp = client.create_tweet(text=text)
    tid = resp.data["id"]
    print(f"Posted! https://x.com/i/web/status/{tid}")
    return {"id": tid, "text": text}


def load_log() -> list:
    path = Path(CONFIG["log_file"])
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_log(logs):
    Path(CONFIG["log_file"]).write_text(
        json.dumps(logs, indent=2), encoding="utf-8")

def log_tweet(data, trend, persona):
    logs = load_log()
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "tweet_id":  data.get("id"),
        "text":      data.get("text"),
        "trend":     trend.get("title"),
        "category":  trend.get("category"),
        "persona":   persona.get("name"),
        "followed_up": False,
    })
    save_log(logs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--show-trends", action="store_true")
    parser.add_argument("--force-cat",   choices=["finance", "fitness"])
    args = parser.parse_args()

    print("AI Tweet Bot v3 - Cloud (Groq)")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}\n")

    # Step 1: Trends
    print("Step 1: Fetching trending topics...")
    trends = get_trending_topics()

    if args.show_trends:
        print("\nFinance trends:")
        for i, t in enumerate(trends.get("finance", [])[:5], 1):
            print(f"  {i}. {t['title']}")
        print("\nFitness trends:")
        for i, t in enumerate(trends.get("fitness", [])[:5], 1):
            print(f"  {i}. {t['title']}")
        return

    if args.force_cat:
        pool = trends.get(args.force_cat, [])
        trend = random.choice(pool) if pool else {
            "title": f"{args.force_cat} tips", "category": args.force_cat}
    else:
        trend = pick_balanced_trend(trends)
    print(f"Trend: {trend['title']}\n")

    # Step 2: Generate using Groq
    persona = random.choice(CONFIG["personas"][trend["category"]])
    print(f"Step 2: Writing as {persona['name']} (via Groq)...")
    try:
        tweet = generate_tweet(trend, persona)
        print(f"Result ({len(tweet)} chars):\n{tweet}\n")
    except ValueError as e:
        print(f"ERROR: {e}")
        return
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Groq API failed: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'no response'}")
        return
    except Exception as e:
        print(f"ERROR generating tweet: {e}")
        return

    # Step 3: Post
    print("Step 3: Posting to Twitter...")
    try:
        result = post_tweet(tweet, dry_run=args.dry_run)
    except tweepy.errors.Unauthorized:
        print("ERROR: Wrong Twitter API keys")
        return
    except tweepy.errors.Forbidden:
        print("ERROR: Twitter app needs Read+Write permissions")
        return
    except ValueError as e:
        print(f"ERROR: {e}")
        return
    except Exception as e:
        print(f"ERROR posting tweet: {e}")
        return

    log_tweet(result, trend, persona)
    print("\nDone!")


if __name__ == "__main__":
    main()
