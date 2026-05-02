from pydantic import BaseModel

class QuoteBase(BaseModel):
    text: str
    author: str
    category: str

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    text: str
    author: str
    category: str

class QuoteResponse(QuoteBase):
    id: int

    class Config:
        from_attributes = True