from sqlalchemy import Column, Integer, String, Text, DateTime, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TwitterEntry(Base):
    __tablename__ = 'twitter_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    link = Column(String(512), nullable=False)
    description = Column(Text)
    published = Column(DateTime)
    tweet_id = Column(String(255), nullable=False, unique=True)
    author = Column(String(255))
    created_at = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')
