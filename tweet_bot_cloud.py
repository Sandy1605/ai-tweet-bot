import sys
import os
import json
import random
import requests
import tweepy
import argparse
from datetime import datetime
from pathlib import Path

# Load .env (local testing only)
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
    # Post a Nordic card every Nth tweet
    "card_every_n": 3,
    "log_file": "tweet_log.json",
}

# ── Nordic card palettes ────────────────────────
NORDIC_PALETTES = [
    {"name": "Arctic Night",  "bg": "0D1B2A", "accent": "4A90D9",
     "style": "deep navy night sky with ice blue aurora"},
    {"name": "Hygge Warm",    "bg": "2C1810", "accent": "E8A838",
     "style": "dark wood interior with candlelight amber warmth"},
    {"name": "Nordic Forest", "bg": "1A2E1A", "accent": "7BC67E",
     "style": "ancient pine forest with moss green light"},
    {"name": "Winter Dawn",   "bg": "1E1E2E", "accent": "CBA6F7",
     "style": "dark winter sky with purple aurora borealis"},
    {"name": "Fjord Blue",    "bg": "0A1628", "accent": "48CAE4",
     "style": "midnight fjord with glacial teal reflections"},
]

# Nordic wisdom themes for card quotes
NORDIC_THEMES = [
    "Danish hygge — finding warmth, contentment and wealth in simple moments",
    "Finnish sisu — inner strength and resilience through life's harshest winters",
    "the Nordic idea that true wealth is freedom, health and community trust",
    "Swedish lagom — perfect balance, not too much not too little, in wealth and life",
    "how surviving harsh Nordic winters builds unbreakable financial and mental resilience",
    "Danish happiness — the world's happiest people find joy in darkness and simplicity",
    "the importance of light returning after long Nordic darkness — hope and new beginnings",
    "Norwegian friluftsliv — how spending time in nature creates wealth of mind and body",
]


# ── Hashtags ────────────────────────────────────
def get_hashtags(category: str, count: int = 3) -> str:
    pool = CONFIG["hashtags"][category].copy()
    random.shuffle(pool)
    selected = pool[:count - 1]
    selected.append(CONFIG["hashtags"]["brand"])
    return " ".join(selected)


# ── Trending topics ─────────────────────────────
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


# ── Generate tweet text via Groq ────────────────
def generate_tweet(trend: dict, persona: dict) -> str:
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
        raise ValueError("GROQ_API_KEY not found!")

    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    r = requests.post(CONFIG["groq"]["url"], headers=headers, json={
        "model": CONFIG["groq"]["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120, "temperature": 0.85,
    }, timeout=30)
    r.raise_for_status()

    text = r.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
    lines = [l for l in text.split("\n") if not l.strip().startswith("#")]
    text = " ".join(lines).strip()

    if len(text) > 180:
        trimmed = text[:180]
        last_end = max(trimmed.rfind('.'), trimmed.rfind('!'), trimmed.rfind('?'))
        if last_end > 80:
            text = trimmed[:last_end + 1]
        else:
            text = trimmed[:trimmed.rfind(' ')] + "."

    return f"{text}\n{sig}\n\n{hashtag_str}"


# ── Nordic card — should we post one? ──────────
def should_post_card() -> bool:
    logs = load_log()
    n = CONFIG["card_every_n"]
    count = 0
    for entry in reversed(logs):
        if entry.get("has_card"):
            break
        count += 1
    return count >= (n - 1)


# ── Generate Nordic quote for card ─────────────
def generate_nordic_quote(tweet_text: str) -> str:
    groq_key = CONFIG["groq"]["key"]
    theme = random.choice(NORDIC_THEMES)
    prompt = f"""Write a short powerful quote inspired by: {theme}

Context — the tweet this card accompanies:
"{tweet_text[:120]}"

Rules:
- Maximum 10 words
- Nordic tone: calm, wise, earned through hardship
- Feels like it was carved in stone or spoken by a Finnish elder
- Universal — no country names
- Output ONLY the quote

Quote:"""

    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    r = requests.post(CONFIG["groq"]["url"], headers=headers, json={
        "model": CONFIG["groq"]["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 25, "temperature": 0.9,
    }, timeout=15)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")


# ── Generate Nordic card image ──────────────────
def generate_nordic_card(tweet_text: str) -> str:
    """
    Creates a Nordic-aesthetic quote card image.
    Uses Pollinations.ai — completely free.
    Returns local image path or None if failed.
    """
    try:
        palette = random.choice(NORDIC_PALETTES)
        quote = generate_nordic_quote(tweet_text)

        print(f"  Card palette: {palette['name']}")
        print(f"  Card quote: {quote}")

        img_prompt = (
            f"minimalist nordic quote card "
            f"dark background {palette['style']} "
            f"elegant serif typography centered quote text "
            f"subtle scandinavian geometric corner accents "
            f"aurora light glow soft edges "
            f"professional instagram square format "
            f"no people no faces "
            f"clean modern nordic design aesthetic"
        ).replace(" ", "%20")

        url = (
            f"https://image.pollinations.ai/prompt/{img_prompt}"
            f"?width=1080&height=1080&nologo=true"
            f"&seed={random.randint(1, 9999)}"
        )

        print(f"  Generating Nordic card image...")
        r = requests.get(url, timeout=45)
        if r.status_code != 200:
            print(f"  Card image failed: {r.status_code}")
            return None

        img_dir = Path("images")
        img_dir.mkdir(exist_ok=True)
        path = str(img_dir / f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        Path(path).write_bytes(r.content)
        print(f"  Nordic card saved!")
        return path

    except Exception as e:
        print(f"  Card error: {e}")
        return None


# ── Post to Twitter ─────────────────────────────
def post_tweet(text: str, image_path: str = None, dry_run: bool = False) -> dict:
    if dry_run:
        print(f"\n[DRY RUN]\n{text}\n{len(text)}/280 chars")
        if image_path:
            print(f"Image: {image_path}")
        return {"id": "dry_run", "text": text}

    cfg = CONFIG["twitter"]
    if not cfg["api_key"]:
        raise ValueError("Twitter API keys not found!")

    media_id = None
    if image_path and Path(image_path).exists():
        try:
            auth = tweepy.OAuth1UserHandler(
                cfg["api_key"], cfg["api_secret"],
                cfg["access_token"], cfg["access_token_secret"])
            api_v1 = tweepy.API(auth)
            media = api_v1.media_upload(filename=image_path)
            media_id = media.media_id
            print(f"  Image uploaded!")
        except Exception as e:
            print(f"  Image upload failed: {e} — posting text only")
            media_id = None

    client = tweepy.Client(
        bearer_token=cfg["bearer_token"],
        consumer_key=cfg["api_key"],
        consumer_secret=cfg["api_secret"],
        access_token=cfg["access_token"],
        access_token_secret=cfg["access_token_secret"],
    )
    kwargs = {"text": text}
    if media_id:
        kwargs["media_ids"] = [media_id]

    resp = client.create_tweet(**kwargs)
    tid = resp.data["id"]
    print(f"  Posted! https://x.com/i/web/status/{tid}")
    return {"id": tid, "text": text}


# ── Log ─────────────────────────────────────────
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

def log_tweet(data, trend, persona, has_card=False):
    logs = load_log()
    logs.append({
        "timestamp":  datetime.now().isoformat(),
        "tweet_id":   data.get("id"),
        "text":       data.get("text"),
        "trend":      trend.get("title"),
        "category":   trend.get("category"),
        "persona":    persona.get("name"),
        "has_card":   has_card,
        "followed_up": False,
    })
    save_log(logs)


# ── Main ────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--show-trends", action="store_true")
    parser.add_argument("--force-card",  action="store_true", help="Force Nordic card this tweet")
    parser.add_argument("--force-cat",   choices=["finance", "fitness"])
    args = parser.parse_args()

    print("AI Tweet Bot v4 - Nordic Edition")
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

    # Step 2: Generate tweet
    persona = random.choice(CONFIG["personas"][trend["category"]])
    print(f"Step 2: Writing as {persona['name']} (Groq)...")
    try:
        tweet = generate_tweet(trend, persona)
        print(f"Result ({len(tweet)} chars):\n{tweet}\n")
    except ValueError as e:
        print(f"ERROR: {e}")
        return
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Groq API failed: {e}")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Step 3: Nordic card (every 3rd tweet)
    with_card = args.force_card or should_post_card()
    card_path = None
    if with_card:
        print("Step 3: Creating Nordic quote card...")
        card_path = generate_nordic_card(tweet)
    else:
        logs = load_log()
        count = 0
        for e in reversed(logs):
            if e.get("has_card"):
                break
            count += 1
        remaining = CONFIG["card_every_n"] - 1 - count
        print(f"Step 3: No card this tweet (next card in {max(0, remaining)} tweets)")

    # Step 4: Post
    print("\nStep 4: Posting to Twitter...")
    try:
        result = post_tweet(tweet, image_path=card_path, dry_run=args.dry_run)
    except tweepy.errors.Unauthorized:
        print("ERROR: Wrong Twitter API keys")
        return
    except tweepy.errors.Forbidden:
        print("ERROR: App needs Read+Write permissions")
        return
    except ValueError as e:
        print(f"ERROR: {e}")
        return
    except Exception as e:
        print(f"ERROR posting: {e}")
        return

    log_tweet(result, trend, persona, has_card=card_path is not None)
    print("\nDone!")


if __name__ == "__main__":
    main()
