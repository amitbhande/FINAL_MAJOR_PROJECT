import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from statsmodels.tsa.stattools import adfuller


@dataclass
class PairAnalyticsResult:
    spread_series: pd.Series
    zscore_series: pd.Series
    hedge_ratio: float
    adf_pvalue: Optional[float]
    rolling_corr: Optional[pd.Series]
    last_updated: float = field(default_factory=time.time)


class AnalyticsEngine:
    """
    Simple in-memory analytics engine operating on pandas DataFrames.

    This is deliberately stateless w.r.t. storage so that in future we can swap
    in a different data backend (e.g., time-series DB) without changing this layer.
    """

    def __init__(self):
        self._lock = threading.Lock()

    def resample_ticks(
        self,
        df: pd.DataFrame,
        timeframe: str,
    ) -> pd.DataFrame:
        """
        Resample tick data into OHLCV for a given timeframe.

        Expects df index to be a DateTimeIndex and columns: ['price', 'qty', 'symbol'].
        """
        if df.empty:
            return df

        ohlcv = df["price"].resample(timeframe).ohlc()
        vol = df["qty"].resample(timeframe).sum().rename("volume")
        out = ohlcv.join(vol, how="outer")
        return out.dropna(how="all")

    def compute_pair_analytics(
        self,
        df_x: pd.DataFrame,
        df_y: pd.DataFrame,
        window: int = 100,
        corr_window: int = 50,
    ) -> Optional[PairAnalyticsResult]:
        """
        Compute hedge ratio (OLS), spread, z-score, ADF test and rolling correlation
        on close prices of two resampled series.
        """
        with self._lock:
            if df_x.empty or df_y.empty:
                return None

            # Align on timestamp
            px = df_x["close"].rename("x")
            py = df_y["close"].rename("y")
            aligned = pd.concat([px, py], axis=1).dropna()
            if len(aligned) < max(window, 20):
                return None

            x = aligned["x"].values
            y = aligned["y"].values

            # OLS hedge ratio y = a + b x
            X = add_constant(x)
            model = OLS(y, X, hasconst=True)
            res = model.fit()
            hedge_ratio = float(res.params[1])

            spread = aligned["y"] - hedge_ratio * aligned["x"]

            if len(spread) < window:
                return None

            rolling_mean = spread.rolling(window).mean()
            rolling_std = spread.rolling(window).std()
            zscore = (spread - rolling_mean) / rolling_std

            # ADF test on latest window of spread
            try:
                adf_res = adfuller(spread.dropna().values[-window:])
                adf_pvalue = float(adf_res[1])
            except Exception:
                adf_pvalue = None

            # Rolling correlation on log returns
            try:
                rx = np.log(aligned["x"]).diff()
                ry = np.log(aligned["y"]).diff()
                rolling_corr = (
                    rx.rolling(corr_window)
                    .corr(ry.rolling(corr_window))
                    .rename("rolling_corr")
                )
            except Exception:
                rolling_corr = None

            return PairAnalyticsResult(
                spread_series=spread,
                zscore_series=zscore,
                hedge_ratio=hedge_ratio,
                adf_pvalue=adf_pvalue,
                rolling_corr=rolling_corr,
            )


