import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
import models

BASE_URL = "https://quotes.toscrape.com"

def scrape_quotes_by_tag(tag: str, limit: int = 20):
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