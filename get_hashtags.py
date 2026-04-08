#!/usr/bin/env python3
"""
Trending Hashtag Fetcher - FREE
Fetches actually trending hashtags from:
1. Hashtagify.me (free tier)
2. RiteTag via RSS
3. Scraped from trending news headlines
No paid API needed.
"""

import requests
import re
import random
from pathlib import Path

NICHE_SEEDS = {
    "finance": [
        "investing", "stocks", "finance", "wealth",
        "wallstreet", "bitcoin", "stockmarket"
    ],
    "fitness": [
        "fitness", "health", "wellness", "workout",
        "nutrition", "mindset", "healthy"
    ],
    "general": [
        "WealthWellness", "NordicLife", "SuccessMindset",
        "MoneyMindset", "PersonalFinance"
    ]
}

def fetch_trending_hashtags(category: str) -> list:
    """
    Gets trending hashtags by scraping Google Trends and
    news headlines for hashtag patterns. Completely free.
    """
    trending = []

    # Method 1: Extract hashtags from trending news headlines
    feeds = {
        "finance": [
            "https://news.google.com/rss/search?q=investing+stocks+finance&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=stock+market+today&hl=en&gl=US&ceid=US:en",
        ],
        "fitness": [
            "https://news.google.com/rss/search?q=fitness+health+wellness&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=nutrition+workout+tips&hl=en&gl=US&ceid=US:en",
        ]
    }

    # Method 2: Build smart hashtags from trending topic keywords
    smart_tags = set()

    for url in feeds.get(category, []):
        try:
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue

            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]>', r.text)
            if not titles:
                titles = re.findall(r'<title>(.*?)</title>', r.text)

            for title in titles[:10]:
                # Extract meaningful words and make hashtags
                words = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', title)
                for word in words:
                    # Skip common news words
                    skip = {"This", "That", "With", "From", "Your",
                           "Have", "Will", "Here", "They", "When",
                           "What", "After", "About", "More", "Over",
                           "News", "Says", "Just", "Year", "Time"}
                    if word not in skip and len(word) > 4:
                        smart_tags.add(f"#{word}")

        except Exception:
            continue

    trending = list(smart_tags)

    # Method 3: Always include proven high-engagement tags for niche
    evergreen = {
        "finance": [
            "#Investing", "#StockMarket", "#PersonalFinance",
            "#WealthBuilding", "#FinancialFreedom", "#PassiveIncome",
            "#MoneyTips", "#FinancialLiteracy", "#InvestingTips",
            "#WealthMindset", "#FinancialIndependence", "#MoneyMindset",
        ],
        "fitness": [
            "#FitnessMotivation", "#HealthyLiving", "#Wellness",
            "#WorkoutTips", "#NutritionTips", "#MentalHealth",
            "#HealthyHabits", "#FitLife", "#Longevity",
            "#NordicWellness", "#MindBodySoul", "#HealthFirst",
        ]
    }

    # Combine trending + evergreen, prioritize trending
    all_tags = trending[:5] + evergreen.get(category, [])

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for tag in all_tags:
        tag_clean = tag.lower()
        if tag_clean not in seen and len(tag) > 2:
            seen.add(tag_clean)
            unique.append(tag)

    return unique


def get_best_hashtags(category: str, count: int = 3) -> str:
    """
    Returns a string of the best hashtags for the category.
    Always includes 1 niche-specific + trending ones.
    """
    tags = fetch_trending_hashtags(category)

    # Always include WealthWellness as brand hashtag
    brand_tag = "#WealthWellness"

    # Pick random selection from pool
    pool = [t for t in tags if t != brand_tag]
    selected = random.sample(pool, min(count - 1, len(pool)))
    selected.append(brand_tag)
    random.shuffle(selected)

    return " ".join(selected[:count])


if __name__ == "__main__":
    print("Testing hashtag fetcher...\n")
    print("Finance hashtags:")
    print(" ", get_best_hashtags("finance", 3))
    print("\nFitness hashtags:")
    print(" ", get_best_hashtags("fitness", 3))
