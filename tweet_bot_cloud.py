import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import random
import requests
import tweepy
import re
import argparse
from datetime import datetime
from pathlib import Path

# Load .env
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
    "ollama": {
        "url":   "http://localhost:11434/api/generate",
        "model": "phi3",
    },

    # BALANCED feeds — 4 finance, 5 fitness
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
            "buffett", "munger", "lynch", "dalio",
            "wealth", "millionaire", "passive income", "financial freedom",
            "portfolio", "dividend", "etf", "net worth",
        ],
        "fitness": [
            "fitness", "workout", "exercise", "health", "longevity", "diet",
            "nutrition", "mental health", "sleep", "weight", "running", "gym",
            "muscle", "protein", "study", "research", "supplement", "wellness",
            "habit", "mindset", "stress", "anxiety", "recovery", "nordic",
            "sauna", "meditation", "calories", "training",
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
            {"name": "a fitness and finance coach",   "signature": "- Fit & Wealthy",
             "style": "connects physical discipline to financial discipline, motivational"},
        ],
    },

    # Curated hashtag pools — proven high engagement, topic-relevant
    # These are NOT company names — they are actual hashtag topics
    "hashtags": {
        "finance": [
            "#Investing", "#StockMarket", "#PersonalFinance", "#FinancialFreedom",
            "#WealthBuilding", "#PassiveIncome", "#MoneyMindset", "#FinancialLiteracy",
            "#InvestingTips", "#WealthMindset", "#StockMarketNews", "#FinanceTwitter",
            "#ValueInvesting", "#DividendInvesting", "#RetirementPlanning",
        ],
        "fitness": [
            "#FitnessMotivation", "#HealthyLiving", "#Wellness", "#WorkoutTips",
            "#MentalHealth", "#HealthyHabits", "#Longevity", "#NordicLife",
            "#MindBody", "#FitLife", "#NutritionTips", "#HealthFirst",
            "#FitnessJourney", "#HealthyMindset", "#WellnessWednesday",
        ],
        "brand": "#WealthWellness",
    },

    # Image every 3rd tweet
    "image_every_n": 3,

    "log_file": str(Path(__file__).parent / "tweet_log.json"),
}


# ── Smart hashtag selector ──────────────────────
def get_hashtags(category: str, count: int = 3) -> str:
    """
    Picks hashtags from curated high-engagement pools.
    Rotates randomly so you never use the same set twice.
    Brand tag always included.
    """
    pool = CONFIG["hashtags"][category].copy()
    random.shuffle(pool)

    # Pick (count-1) from category pool + always add brand tag
    selected = pool[:count - 1]
    selected.append(CONFIG["hashtags"]["brand"])

    return " ".join(selected)


# ── Trending topics from Google News RSS (FREE) ─
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
                kws = CONFIG["keywords"][category]
                if any(kw in title.lower() for kw in kws):
                    found[category].append(
                        {"title": title, "category": category})
        except Exception:
            continue

    # Deduplicate
    result = {}
    for cat, items in found.items():
        seen, unique = set(), []
        for t in items:
            if t["title"] not in seen:
                seen.add(t["title"])
                unique.append(t)
        result[cat] = unique

    print(f"  Finance: {len(result.get('finance',[]))} | Fitness: {len(result.get('fitness',[]))}")
    return result


def pick_balanced_trend(trends: dict) -> dict:
    """Always alternates between finance and fitness."""
    log = load_log()
    recent = [e for e in log[-6:] if "category" in e]
    fin = sum(1 for e in recent if e["category"] == "finance")
    fit = sum(1 for e in recent if e["category"] == "fitness")

    # Pick whichever category has fewer recent posts
    if fit <= fin and trends.get("fitness"):
        cat = "fitness"
    elif trends.get("finance"):
        cat = "finance"
    else:
        cat = "fitness" if trends.get("fitness") else "finance"

    pool = trends.get(cat, [])
    if not pool:
        pool = [{"title": f"building healthy {cat} habits daily", "category": cat}]

    print(f"  Picked: {cat} (recent: finance={fin} fitness={fit})")
    return random.choice(pool[:5])


# ── Should this tweet have an image? ───────────
def should_post_image() -> bool:
    logs = load_log()
    n = CONFIG["image_every_n"]
    count = 0
    for entry in reversed(logs):
        if entry.get("has_image"):
            break
        count += 1
    return count >= (n - 1)


# ── Generate image FREE (Pollinations.ai) ──────
def generate_image(trend: dict) -> str | None:
    try:
        category = trend["category"]
        if category == "finance":
            style = "minimalist financial chart illustration, nordic clean design, professional"
        else:
            style = "nordic nature wellness lifestyle, calm forest, fitness motivation, clean"

        topic = trend["title"][:60].replace(" ", "%20")
        style_enc = style.replace(" ", "%20").replace(",", "%2C")
        url = f"https://image.pollinations.ai/prompt/{style_enc}%20{topic}?width=1200&height=675&nologo=true"

        print(f"  Generating image (free, Pollinations.ai)...")
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return None

        img_dir = Path(__file__).parent / "images"
        img_dir.mkdir(exist_ok=True)
        img_path = img_dir / f"tweet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        img_path.write_bytes(r.content)
        print(f"  Image saved: {img_path.name}")
        return str(img_path)
    except Exception as e:
        print(f"  Image failed: {e}")
        return None


# ── Generate tweet with Ollama (FREE, local) ───
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

    r = requests.post(CONFIG["ollama"]["url"], json={
        "model": CONFIG["ollama"]["model"],
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.85},
    }, timeout=180)
    r.raise_for_status()

    text = r.json()["response"].strip().strip('"').strip("'")
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


# ── Post to Twitter (1 API credit) ─────────────
def post_tweet(text: str, image_path: str = None,
               dry_run: bool = False) -> dict:
    if dry_run:
        print(f"\n  [DRY RUN - not posted]")
        print(f"  {'─'*50}\n  {text}\n  {'─'*50}")
        print(f"  {len(text)}/280 chars")
        if image_path:
            print(f"  Image: {image_path}")
        return {"id": "dry_run", "text": text}

    cfg = CONFIG["twitter"]
    if not cfg["api_key"]:
        raise ValueError("No API keys in .env!")

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

def log_tweet(data, trend, persona, has_image=False):
    logs = load_log()
    logs.append({
        "timestamp":   datetime.now().isoformat(),
        "tweet_id":    data.get("id"),
        "text":        data.get("text"),
        "trend":       trend.get("title"),
        "category":    trend.get("category"),
        "persona":     persona.get("name"),
        "has_image":   has_image,
        "followed_up": False,
    })
    save_log(logs)


# ── Main ────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--show-trends", action="store_true")
    parser.add_argument("--force-image", action="store_true")
    parser.add_argument("--force-cat",   choices=["finance", "fitness"])
    args = parser.parse_args()

    print("\nAI Tweet Bot v3 - Balanced Finance + Fitness")
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
        print("\nSample hashtags (these rotate randomly each tweet):")
        print(f"  Finance: {get_hashtags('finance', 3)}")
        print(f"  Finance: {get_hashtags('finance', 3)}")
        print(f"  Fitness: {get_hashtags('fitness', 3)}")
        print(f"  Fitness: {get_hashtags('fitness', 3)}")
        return

    # Pick trend
    if args.force_cat:
        pool = trends.get(args.force_cat, [])
        trend = random.choice(pool) if pool else {
            "title": f"{args.force_cat} tips", "category": args.force_cat}
    else:
        trend = pick_balanced_trend(trends)
    print(f"  Trend: {trend['title']}\n")

    # Step 2: Generate
    persona = random.choice(CONFIG["personas"][trend["category"]])
    print(f"Step 2: Writing as {persona['name']}...")
    try:
        tweet = generate_tweet(trend, persona)
        print(f"  Result ({len(tweet)} chars):\n  {tweet}\n")
    except requests.exceptions.ConnectionError:
        print("ERROR: Ollama not running! Run: ollama serve")
        return
    except requests.exceptions.ReadTimeout:
        print("ERROR: Ollama timed out. Is phi3 downloaded?")
        return

    # Step 3: Image (every 3rd tweet)
    with_image = args.force_image or should_post_image()
    image_path = None
    if with_image:
        print("Step 3: Generating image...")
        image_path = generate_image(trend)
    else:
        logs = load_log()
        count_since = 0
        for e in reversed(logs):
            if e.get("has_image"):
                break
            count_since += 1
        remaining = CONFIG["image_every_n"] - 1 - count_since
        print(f"Step 3: No image (next image in {max(0,remaining)} tweets)")

    # Step 4: Post
    print("\nStep 4: Posting...")
    try:
        result = post_tweet(tweet, image_path=image_path,
                           dry_run=args.dry_run)
    except tweepy.errors.Unauthorized:
        print("ERROR: Wrong API keys")
        return
    except tweepy.errors.Forbidden:
        print("ERROR: Need Read+Write permissions")
        return
    except ValueError as e:
        print(f"ERROR: {e}")
        return

    log_tweet(result, trend, persona, has_image=image_path is not None)
    print("\nDone!\n")


if __name__ == "__main__":
    main()
