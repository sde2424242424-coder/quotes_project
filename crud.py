from sqlalchemy.orm import Session
import models
import schemas

def create_quote(db: Session, quote: schemas.QuoteCreate):
    db_quote = models.Quote(
        text=quote.text,
        author=quote.author,
        category=quote.category
    )
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def get_quotes(db: Session):
    return db.query(models.Quote).all()

def get_quote(db: Session, quote_id: int):
    return db.query(models.Quote).filter(models.Quote.id == quote_id).first()

def update_quote(db: Session, quote_id: int, quote: schemas.QuoteUpdate):
    db_quote = get_quote(db, quote_id)
    if not db_quote:
        return None

    db_quote.text = quote.text
    db_quote.author = quote.author
    db_quote.category = quote.category
    db.commit()
    db.refresh(db_quote)
    return db_quote

def delete_quote(db: Session, quote_id: int):
    db_quote = get_quote(db, quote_id)
    if not db_quote:
        return None

    db.delete(db_quote)
    db.commit()
    return db_quote