from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import gradio as gr

from database import Base, engine, get_db
import models
import schemas
import crud
from crawler import scrape_quotes_by_tag, save_quotes_to_db
from gradio_app import build_gradio

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Quotes Management API")

@app.get("/")
def root():
    return {"message": "Quotes API is running"}

@app.post("/quotes/", response_model=schemas.QuoteResponse)
def create_quote(quote: schemas.QuoteCreate, db: Session = Depends(get_db)):
    return crud.create_quote(db, quote)

@app.get("/quotes/", response_model=list[schemas.QuoteResponse])
def read_quotes(db: Session = Depends(get_db)):
    return crud.get_quotes(db)

@app.get("/quotes/search/{keyword}")
def search_quotes(keyword: str, db: Session = Depends(get_db)):
    return db.query(models.Quote).filter(
        models.Quote.text.ilike(f"%{keyword}%")
    ).all()

@app.get("/quotes/author/{author}")
def get_by_author(author: str, db: Session = Depends(get_db)):
    return db.query(models.Quote).filter(
        models.Quote.author.ilike(f"%{author}%")
    ).all()

@app.get("/quotes/{quote_id}", response_model=schemas.QuoteResponse)
def read_quote(quote_id: int, db: Session = Depends(get_db)):
    quote = crud.get_quote(db, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@app.put("/quotes/{quote_id}", response_model=schemas.QuoteResponse)
def update_quote(quote_id: int, quote: schemas.QuoteUpdate, db: Session = Depends(get_db)):
    updated = crud.update_quote(db, quote_id, quote)
    if not updated:
        raise HTTPException(status_code=404, detail="Quote not found")
    return updated

@app.delete("/quotes/{quote_id}")
def delete_quote(quote_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_quote(db, quote_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"message": "Quote deleted successfully"}

@app.post("/crawl/{tag}")
def crawl_quotes(tag: str, db: Session = Depends(get_db)):
    quotes_data = scrape_quotes_by_tag(tag, limit=20)
    added = save_quotes_to_db(db, quotes_data)
    return {
        "tag": tag,
        "scraped": len(quotes_data),
        "added_to_db": added
    }

demo = build_gradio()
app = gr.mount_gradio_app(app, demo, path="/gradio")