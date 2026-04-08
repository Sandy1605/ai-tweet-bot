"""
Nordic Quote Card Generator
Creates beautiful quote card images with Nordic aesthetic
Uses only Python standard library + requests (no PIL needed)
Generates HTML canvas cards via Pollinations.ai image API
"""

import os
import requests
import random
from pathlib import Path
from datetime import datetime

# Nordic color palettes — rotates between these
NORDIC_PALETTES = [
    {
        "name": "Arctic Night",
        "bg": "#0D1B2A",
        "accent": "#4A90D9",
        "text": "#E8F4FD",
        "sub": "#7FB3D3",
        "desc": "deep navy with ice blue — harsh winter night sky"
    },
    {
        "name": "Hygge Warm",
        "bg": "#2C1810",
        "accent": "#E8A838",
        "text": "#FAF0E6",
        "sub": "#D4956A",
        "desc": "dark wood brown with candlelight amber — hygge warmth"
    },
    {
        "name": "Nordic Forest",
        "bg": "#1A2E1A",
        "accent": "#7BC67E",
        "text": "#E8F5E8",
        "sub": "#9AC99D",
        "desc": "deep pine green with moss — Scandinavian forest"
    },
    {
        "name": "Winter Dawn",
        "bg": "#1E1E2E",
        "accent": "#CBA6F7",
        "text": "#CDD6F4",
        "sub": "#A6ADC8",
        "desc": "dark slate with aurora purple — Nordic winter dawn"
    },
    {
        "name": "Fjord Blue",
        "bg": "#0A1628",
        "accent": "#48CAE4",
        "text": "#E0F4FF",
        "sub": "#90C4D8",
        "desc": "midnight fjord with glacial teal"
    },
]

# Nordic wisdom themes for quote prompts
NORDIC_THEMES = [
    "the Danish concept of hygge — finding warmth and contentment in simple moments",
    "Finnish sisu — inner strength and resilience through life's harshest winters",
    "the Norwegian concept of friluftsliv — finding freedom and wealth in nature",
    "Nordic trust — why Scandinavian societies are the happiest and most prosperous",
    "the Swedish lagom philosophy — not too much, not too little — perfect balance in wealth",
    "how Nordic countries survive harsh winters by building strong communities and inner wealth",
    "the connection between physical wellness in cold climates and financial resilience",
    "Danish happiness secrets — why the world's happiest people live in the darkest country",
    "the importance of light in Nordic winters — finding hope and growth in darkness",
    "Finnish relationship with silence and nature as the foundation of true wealth",
]


def generate_nordic_quote(groq_key: str, theme: str, tweet_text: str) -> str:
    """Generate a short punchy quote for the card using Groq."""
    prompt = f"""Create a short, powerful quote card text inspired by {theme}.

The tweet being paired with this card:
"{tweet_text}"

Write a SHORT quote for a visual card (max 12 words).
The quote should feel Nordic — calm, wise, slightly cold but deeply meaningful.
Like something carved in stone in a Finnish sauna or painted on a Danish cottage wall.
Do NOT mention specific countries by name.
Output ONLY the quote text, nothing else.

Quote:"""

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 40,
        "temperature": 0.9,
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=payload, timeout=15
    )
    r.raise_for_status()
    quote = r.json()["choices"][0]["message"]["content"].strip()
    quote = quote.strip('"').strip("'")
    return quote


def generate_card_image(quote: str, palette: dict, output_dir: str) -> str:
    """
    Generate a Nordic quote card image using Pollinations.ai.
    Returns path to saved image.
    """
    # Build a detailed image generation prompt
    img_prompt = (
        f"minimalist nordic quote card, dark background color {palette['bg']}, "
        f"elegant typography, quote text: '{quote}', "
        f"subtle nordic geometric pattern border, "
        f"accent color {palette['accent']}, "
        f"scandinavian design aesthetic, clean modern layout, "
        f"soft aurora light effect in background corners, "
        f"professional social media card format 1:1 ratio, "
        f"no watermark, high quality"
    )

    # URL encode
    encoded = img_prompt.replace(" ", "%20").replace("'", "%27").replace(",", "%2C").replace(":", "%3A").replace("#", "%23")

    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&nologo=true&seed={random.randint(1,9999)}"

    print(f"  Generating Nordic card ({palette['name']})...")
    r = requests.get(url, timeout=45)
    if r.status_code != 200:
        print(f"  Card generation failed: {r.status_code}")
        return None

    Path(output_dir).mkdir(exist_ok=True)
    filename = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = str(Path(output_dir) / filename)
    Path(filepath).write_bytes(r.content)
    print(f"  Card saved: {filename}")
    return filepath


def create_nordic_card(tweet_text: str, groq_key: str, output_dir: str = "images") -> str:
    """
    Main function — creates a complete Nordic quote card.
    Returns path to image file or None if failed.
    """
    try:
        # Pick random palette and theme
        palette = random.choice(NORDIC_PALETTES)
        theme = random.choice(NORDIC_THEMES)

        print(f"  Palette: {palette['name']} — {palette['desc']}")
        print(f"  Theme: {theme[:50]}...")

        # Generate the quote
        quote = generate_nordic_quote(groq_key, theme, tweet_text)
        print(f"  Quote: {quote}")

        # Generate the card image
        image_path = generate_card_image(quote, palette, output_dir)
        return image_path

    except Exception as e:
        print(f"  Card creation error: {e}")
        return None


# Test
if __name__ == "__main__":
    import sys
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        # Try loading .env
        env = Path(".env")
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("GROQ_API_KEY="):
                    key = line.split("=", 1)[1].strip()

    if not key:
        print("No GROQ_API_KEY found")
        sys.exit(1)

    test_tweet = "Discipline is choosing what you want most over what you want now."
    print(f"Test tweet: {test_tweet}\n")
    path = create_nordic_card(test_tweet, key, "images")
    if path:
        print(f"\nCard created: {path}")
    else:
        print("Card creation failed")
