import threading
import time
from typing import Dict, List

import pandas as pd
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Tick(Base):
    __tablename__ = "ticks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(Float, index=True)  # epoch milliseconds
    symbol = Column(String(20), index=True)
    price = Column(Float)
    qty = Column(Float)


class DataStore:
    """
    Thin wrapper around SQLite via SQLAlchemy.

    Responsible only for persistence and retrieval; keeps analytics concerns out.
    """

    def __init__(self, db_url: str = "sqlite:///ticks.db"):
        self.engine = create_engine(db_url, future=True)
        Base.metadata.create_all(self.engine)
        self._lock = threading.Lock()

    def insert_tick(self, ts_ms: float, symbol: str, price: float, qty: float) -> None:
        with self._lock, Session(self.engine) as session:
            t = Tick(ts=ts_ms, symbol=symbol, price=price, qty=qty)
            session.add(t)
            session.commit()

    def get_ticks_df(
        self,
        symbol: str,
        lookback_seconds: int = 3600,
    ) -> pd.DataFrame:
        """
        Load ticks for a symbol over a recent lookback window into a DataFrame.
        """
        now_ms = time.time() * 1000
        from_ts = now_ms - lookback_seconds * 1000

        with self._lock, Session(self.engine) as session:
            rows: List[Tick] = (
                session.query(Tick)
                .filter(Tick.symbol == symbol, Tick.ts >= from_ts)
                .order_by(Tick.ts)
                .all()
            )

        if not rows:
            return pd.DataFrame(columns=["ts", "symbol", "price", "qty"])

        df = pd.DataFrame(
            [
                {
                    "ts": r.ts,
                    "symbol": r.symbol,
                    "price": r.price,
                    "qty": r.qty,
                }
                for r in rows
            ]
        )
        df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)
        return df[["symbol", "price", "qty"]]


