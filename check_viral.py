#!/usr/bin/env python3
"""
Viral Tweet Checker — run ONCE per day
- Reads metrics for today's tweets only (3 API reads = $0.015)
- If any tweet has 500+ impressions, posts ONE follow-up ($0.01)
- Total max cost per day: $0.025
- Has duplicate protection — never posts same follow-up twice
"""

import os
import json
import random
import requests
import tweepy
from datetime import datetime, date
from pathlib import Path

# ── Load .env ──────────────────────────────────
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

VIRAL_THRESHOLD = 500   # impressions needed to trigger follow-up
LOG_FILE = Path(__file__).parent / "tweet_log.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def load_log():
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_log(logs):
    LOG_FILE.write_text(json.dumps(logs, indent=2), encoding="utf-8")


def get_twitter_client():
    return tweepy.Client(
        bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
    )


def check_viral_once():
    logs = load_log()
    today = date.today().isoformat()

    # Only check tweets from TODAY that haven't been checked yet
    todays_tweets = [
        e for e in logs
        if e.get("tweet_id")
        and e["tweet_id"] != "dry_run"
        and e["timestamp"][:10] == today
        and not e.get("metrics_checked_today")
        and not e.get("followed_up")
    ]

    if not todays_tweets:
        print("No new tweets to check today.")
        return

    print(f"Checking {len(todays_tweets)} tweets from today...")
    print(f"Cost: {len(todays_tweets)} × $0.005 = ${len(todays_tweets) * 0.005:.3f}")

    client = get_twitter_client()
    viral_tweet = None

    for entry in todays_tweets:
        try:
            result = client.get_tweet(
                entry["tweet_id"],
                tweet_fields=["public_metrics"]
            )
            if not result.data:
                continue

            metrics = result.data.public_metrics
            impressions = metrics.get("impression_count", 0)
            likes       = metrics.get("like_count", 0)
            retweets    = metrics.get("retweet_count", 0)

            print(f"  [{entry['tweet_id']}] {impressions} impressions | {likes} likes | {retweets} RTs")

            # Save metrics to log
            entry["impressions"]          = impressions
            entry["likes"]                = likes
            entry["retweets"]             = retweets
            entry["metrics_checked_today"] = True

            # Pick highest performing tweet
            if impressions >= VIRAL_THRESHOLD:
                if viral_tweet is None or impressions > viral_tweet.get("impressions", 0):
                    viral_tweet = entry

        except Exception as e:
            print(f"  Could not read tweet {entry['tweet_id']}: {e}")
            entry["metrics_checked_today"] = True

    save_log(logs)

    if not viral_tweet:
        print(f"\nNo viral tweets yet (threshold: {VIRAL_THRESHOLD} impressions).")
        print("Keep posting consistently — growth takes time!")
        return

    # ── Viral tweet found! Post follow-up ──
    print(f"\n🔥 Viral tweet! {viral_tweet['impressions']} impressions")
    print(f"   Original: {viral_tweet['text'][:100]}...")

    # Generate follow-up with Ollama (free)
    prompt = f"""A tweet just went viral with {viral_tweet['impressions']} impressions:

"{viral_tweet['text']}"

Write a follow-up tweet that:
- Expands on the same idea with a NEW angle
- Stands completely alone (no "as I mentioned" or "earlier I said")
- Is punchy and shareable
- Max 200 characters
- No hashtags
- Output tweet text only

Follow-up:"""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.8},
        }, timeout=90)
        followup_text = r.json()["response"].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Ollama error: {e}")
        return

    # Pick hashtags from original tweet category
    category = viral_tweet.get("category", "finance")
    if category == "fitness":
        hashtags = "#WealthWellness #NordicLife #Health"
    else:
        hashtags = "#WealthWellness #Investing #FinancialFreedom"

    full_tweet = f"{followup_text}\n\n{hashtags}"
    if len(full_tweet) > 280:
        full_tweet = f"{followup_text[:240]}...\n\n{hashtags}"

    print(f"\nFollow-up ({len(full_tweet)} chars):")
    print(f"  {full_tweet}")
    print(f"\nPosting follow-up (cost: $0.01)...")

    try:
        resp = client.create_tweet(text=full_tweet)
        followup_id = resp.data["id"]
        print(f"Posted! https://x.com/i/web/status/{followup_id}")

        # Mark original as followed up
        viral_tweet["followed_up"]  = True
        viral_tweet["followup_id"]  = followup_id
        save_log(logs)

        # Log follow-up tweet too
        logs2 = load_log()
        logs2.append({
            "timestamp": datetime.now().isoformat(),
            "tweet_id":  followup_id,
            "text":      full_tweet,
            "trend":     viral_tweet.get("trend", "follow-up"),
            "category":  category,
            "persona":   "viral-followup",
            "is_followup": True,
            "original_id": viral_tweet["tweet_id"],
        })
        save_log(logs2)

    except Exception as e:
        print(f"Could not post follow-up: {e}")


if __name__ == "__main__":
    print("\n📊 Viral Tweet Checker")
    print(f"   Threshold: {VIRAL_THRESHOLD} impressions")
    print(f"   Date: {date.today()}\n")
    check_viral_once()
    print("\nDone.\n")
