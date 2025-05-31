from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone
from config import DATABASE_URL

Base = declarative_base()

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pair_address = Column(String, unique=True, index=True, nullable=False)
    chain_id = Column(String, nullable=False, index=True)
    dex_id = Column(String)
    url = Column(String)
    base_token_address = Column(String, index=True, nullable=False)
    base_token_name = Column(String)
    base_token_symbol = Column(String, index=True)
    quote_token_symbol = Column(String)
    price_usd = Column(Float, nullable=True)
    price_native = Column(Float, nullable=True)
    volume_h24 = Column(Float, nullable=True)
    volume_h6 = Column(Float, nullable=True)
    volume_h1 = Column(Float, nullable=True)
    price_change_h24 = Column(Float, nullable=True)
    price_change_h6 = Column(Float, nullable=True)
    price_change_h1 = Column(Float, nullable=True)
    liquidity_usd = Column(Float, nullable=True)
    fdv = Column(Float, nullable=True)
    market_cap_usd = Column(Float, nullable=True)
    pair_created_at = Column(DateTime(timezone=True), nullable=True)
    holders = Column(Integer, nullable=True)
    passed_dex_filters = Column(Boolean, default=False, index=True)
    is_pumpfun_launch = Column(Boolean, default=False, index=True)
    pumpfun_mint_address = Column(String, unique=True, nullable=True, index=True)
    pumpfun_metadata = Column(JSON, nullable=True)
    market_state = Column(String, nullable=True, index=True)
    last_ema_short = Column(Float, nullable=True)
    ema_short_slope = Column(Float, nullable=True)
    last_ema_long = Column(Float, nullable=True)
    ema_long_slope = Column(Float, nullable=True)
    rsi_value = Column(Float, nullable=True)
    volatility_bands_data = Column(JSON, nullable=True)
    last_trend_analysis_at = Column(DateTime(timezone=True), nullable=True)
    gmgn_trade_status = Column(String, nullable=True, index=True)
    gmgn_last_order_id = Column(String, nullable=True)
    gmgn_buy_price_usd = Column(Float, nullable=True)
    gmgn_buy_timestamp = Column(DateTime(timezone=True), nullable=True)
    gmgn_sell_price_usd = Column(Float, nullable=True)
    gmgn_sell_timestamp = Column(DateTime(timezone=True), nullable=True)
    continuously_monitor = Column(Boolean, default=False, index=True)
    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_dexscreener_fetch_at = Column(DateTime(timezone=True), nullable=True)
    social_links_raw = Column(JSON, nullable=True)
    social_links_verified_status = Column(String, default="PENDING", index=True)
    verified_social_links = Column(JSON, nullable=True)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    pumpfun_last_fetched = Column(DateTime(timezone=True))
    fetch_error_count = Column(Integer, default=0)


class InsiderTransaction(Base):
    __tablename__ = "insider_transactions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    wallet_address = Column(String, index=True, nullable=False)
    token_address = Column(String, index=True, nullable=False)
    transaction_type = Column(String, nullable=False)
    amount_tokens = Column(Float, nullable=True)
    amount_usd = Column(Float, nullable=True)
    transaction_hash = Column(String, unique=True, nullable=False)
    source = Column(String, default="GMGN")
    notes = Column(String, nullable=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized and tables created (if they didn't exist).")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
