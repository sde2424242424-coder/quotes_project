import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
import models

BASE_URL = "https://quotes.toscrape.com"

DEFAULT_TAGS = [
    "love",
    "inspirational",
    "life",
    "humor",
    "books",
    "reading",
    "friendship",
    "friends",
    "truth",
    "simile",
    "success",
    "value",
    "failure",
    "classic",
    "literature",
    "writing",
    "poetry",
    "religion",
    "happiness",
    "comedy",
    "children",
    "imagination",
    "music",
    "marriage",
    "philosophy",
    "romance",
    "yourself"
]

MAX_QUOTES_LIMIT = 100


def scrape_quotes_by_tag(tag: str, limit: int = MAX_QUOTES_LIMIT):
    quotes = []
    page = 1

    while len(quotes) < limit:
        url = f"{BASE_URL}/tag/{tag}/page/{page}/"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".quote")

        if not items:
            break

        for item in items:
            text = item.select_one(".text").get_text(strip=True)
            author = item.select_one(".author").get_text(strip=True)

            quotes.append({
                "text": text,
                "author": author,
                "category": tag
            })

            if len(quotes) >= limit:
                break

        page += 1

    return quotes


def scrape_quotes_by_default_tags(limit_per_tag: int = MAX_QUOTES_LIMIT):
    all_quotes = []

    for tag in DEFAULT_TAGS:
        quotes = scrape_quotes_by_tag(tag, limit_per_tag)
        all_quotes.extend(quotes)

    return all_quotes


def scrape_quotes_until_total_limit(total_limit: int = MAX_QUOTES_LIMIT):
    all_quotes = []
    seen = set()

    for tag in DEFAULT_TAGS:
        quotes = scrape_quotes_by_tag(tag, total_limit)

        for q in quotes:
            unique_key = (q["text"], q["author"])

            if unique_key not in seen:
                seen.add(unique_key)
                all_quotes.append(q)

            if len(all_quotes) >= total_limit:
                return all_quotes

    return all_quotes


def save_quotes_to_db(db: Session, quotes_data):
    added = 0

    for q in quotes_data:
        exists = db.query(models.Quote).filter(
            models.Quote.text == q["text"],
            models.Quote.author == q["author"]
        ).first()

        if not exists:
            quote = models.Quote(
                text=q["text"],
                author=q["author"],
                category=q["category"]
            )
            db.add(quote)
            added += 1

    db.commit()
    return added