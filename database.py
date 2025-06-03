# database.py additions/updates
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timezone
from config import DATABASE_URL

Base = declarative_base()

class Database:
    def __init__(self, db_path=None):
        # Use DATABASE_URL from config or override with db_path
        from config import DATABASE_URL
        self.engine = create_engine(DATABASE_URL if db_path is None else f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def initialize(self):
        Base.metadata.create_all(self.engine)

    def add_token(self, token_data):
        token = Token(**token_data)
        self.session.add(token)
        self.session.commit()

    def token_exists(self, mint_address):
        return self.session.query(Token).filter_by(pumpfun_mint_address=mint_address).first() is not None

    def close(self):
        self.session.close()

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
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# def init_db():
#     Base.metadata.create_all(engine)

# def get_db_session():
#     return SessionLocal()

SessionLocal = sessionmaker(bind=init_db())
