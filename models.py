from sqlalchemy import Column, Integer, String, Text
from database import Base

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)