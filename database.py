# database.py additions/updates
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timezone
from config import DATABASE_URL

Base = declarative_base()

class Token(Base):
    __tablename__ = 'tokens'
    
    id = Column(Integer, primary_key=True)
    pumpfun_mint_address = Column(String(44), unique=True, index=True)
    dexscreener_pair_address = Column(String(44), unique=True, index=True, nullable=True)
    
    # Token metadata
    name = Column(String(255))
    symbol = Column(String(20))
    description = Column(Text)
    
    # Classification flags
    is_pumpfun_launch = Column(Boolean, default=False)
    is_dexscreener_tracked = Column(Boolean, default=False)
    
    # Chain information
    chain_id = Column(String(20), default="solana")
    
    # Metadata storage
    pumpfun_metadata = Column(JSON)
    dexscreener_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Trading metrics (can be populated later)
    market_cap = Column(String(50))
    price_usd = Column(String(50))
    volume_24h = Column(String(50))
    
    def __repr__(self):
        return f"<Token(mint={self.pumpfun_mint_address}, name={self.name})>"

# Database initialization
def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_db_session():
    engine = init_db()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

SessionLocal = sessionmaker(bind=init_db())
