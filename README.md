## Quant Analytics Demo – Binance Pairs Trading Helper

This is a **lightweight demo app** that ingests live tick data from Binance, stores it in SQLite, runs basic pair-trading analytics, and exposes an interactive dashboard in a single Python process.

The focus is on **clarity, modularity and end‑to‑end flow**, not on production‑scale engineering.

### 1. Features

- **Live data ingestion**
  - Connects to Binance WebSocket trade streams for a small set of spot symbols (`BTCUSDT`, `ETHUSDT`, `BNBUSDT`).
  - Stores all incoming ticks (`timestamp, symbol, price, qty`) into a local **SQLite** database via SQLAlchemy.
  - Design is easily extendable to other feeds (REST, CSV, different exchanges).

- **Sampling / resampling**
  - On demand, loads recent ticks for a symbol and resamples into OHLCV using pandas.
  - Supported timeframes: **1s**, **1m**, **5m**.

- **Core analytics**
  - **Hedge ratio via OLS regression**: `Y ~ X`, hedge ratio = slope (`beta`).
  - **Spread**: `spread = price_y − beta * price_x`.
  - **Z‑score** of spread over rolling window (configurable).
  - **ADF test** on spread (last `window` points) to check for mean‑reversion / stationarity.
  - **Rolling correlation** of log returns between the two legs.
  - All analytics implemented in a small, isolated `AnalyticsEngine`.

- **Frontend (Dash / Plotly)**
  - Interactive dashboard with:
    - Symbol selection for **X** and **Y** legs.
    - Timeframe, rolling window, and alert threshold controls.
    - Live‑updating charts:
      - Prices of both legs + spread overlay.
      - Z‑score vs time with ±2 bands.
      - Rolling correlation of log returns.
  - Charts support **zoom / pan / hover** via Plotly.
  - **ADF test button** triggers on‑demand spread stationarity check.
  - Multiple products supported by simply choosing different pairs.

- **Alerts**
  - Simple, rule‑based alert: **`|z| >= threshold`**.
  - Banner text highlights when the latest z‑score exceeds the configured threshold and suggests trade direction (long/short spread).

- **Data export / upload**
  - **Export** current pair analytics (spread & z‑score) as CSV from the live view.
  - **Upload** OHLC CSV (e.g., historical data) to run the same style of z‑score analytics purely on uploaded data.
  - Supports timestamp column named `timestamp` or `time`, and a `close` column.

### 2. Getting Started

#### 2.1. Install dependencies

From the project root:

```bash
python -m venv .venv
.\.venv\Scripts\activate        # on Windows PowerShell
pip install -r requirements.txt
```

#### 2.2. Run the app

```bash
python app.py
```

Then open the printed local URL (typically `http://127.0.0.1:8050`) in your browser.

The app will:

- start a background **Binance WebSocket ingestor**,
- continuously store ticks into `ticks.db` (SQLite),
- and serve the Dash dashboard.

### 3. How the System Is Structured

- `binance_ingestor.py`
  - Minimal WebSocket client for Binance trade streams.
  - Runs in its own thread with an asyncio loop.
  - Writes each trade into the `DataStore` as it arrives.

- `data_store.py`
  - Wraps **SQLite + SQLAlchemy**.
  - Schema: single `ticks` table: `id, ts, symbol, price, qty`.
  - Methods:
    - `insert_tick(...)` for ingestion.
    - `get_ticks_df(symbol, lookback_seconds)` returns a pandas DataFrame indexed by timestamp.

- `analytics_engine.py`
  - Stateless analytics layer that operates on pandas DataFrames.
  - Entry points:
    - `resample_ticks(df, timeframe)` → OHLCV DataFrame.
    - `compute_pair_analytics(df_x, df_y, window, corr_window)` → hedge ratio, spread, z‑score, ADF p‑value, rolling correlation.
  - This isolation makes it easy to:
    - swap out the storage layer, or
    - add new analytics (e.g., Kalman filter, robust regression) without touching ingestion or UI.

- `app.py`
  - Single **Dash app** which:
    - Starts the ingestor.
    - Provides user controls and graphs.
    - Periodically pulls recent ticks via `DataStore`, resamples via `AnalyticsEngine`, and renders charts.
    - Handles alerts, downloads, and OHLC upload analytics.

### 4. Architecture & Design Notes

- **Loose coupling**
  - Ingestion → `BinanceIngestor` only depends on `DataStore`.
  - Storage → `DataStore` only knows about SQLite.
  - Analytics → `AnalyticsEngine` only consumes pandas DataFrames.
  - UI → `app.py` only calls well‑defined methods on `DataStore` and `AnalyticsEngine`.

- **Extensibility**
  - To add a new data source (e.g., CME futures):
    - Implement another ingestor class that writes into `DataStore` or another store with the same interface.
  - To add new analytics:
    - Extend `AnalyticsEngine` with new functions and wire new endpoints / callbacks in `app.py`.
  - To support more complex alerts:
    - Add an alert rules module that evaluates analytics outputs and pushes messages / notifications.

- **Scaling considerations (future)**
  - Replace SQLite with a time‑series database or Postgres, but keep `DataStore` interface similar.
  - Move ingestion to a separate service (e.g., container) writing to a shared DB / bus, while Dash consumes via HTTP/SQL.
  - Introduce caching for computed analytics if many users / heavy windows.

### 5. Example Analytics Interpretation

- **Hedge ratio (beta)**: for a pair like BTCUSDT (X) and ETHUSDT (Y), beta represents the notional ratio required to hedge moves in Y with X.
- **Spread**: deviation between Y and beta‑hedged X; a mean‑reverting spread is a candidate for statistical arbitrage.
- **Z‑score**:
  - High positive z‑score → spread is above its rolling mean → potential **short‑spread** (short Y, long X).
  - High negative z‑score → spread is below its rolling mean → potential **long‑spread** (long Y, short X).
- **ADF p‑value**:
  - Low p‑value (< ~0.05) suggests the spread is stationary over the chosen window, supporting a mean‑reversion strategy.
- **Rolling correlation**:
  - Helps understand co‑movement of returns; low or unstable correlation may question the stability of the hedge.

### 6. Uploading OHLC Data

- Upload a CSV with:
  - `timestamp` or `time` column (parseable to datetime).
  - `close` column.
- The app will:
  - Plot the close series.
  - Compute a simple rolling z‑score on the close price (window=50).
  - Allow CSV export of these uploaded‑data analytics as well.

### 7. ChatGPT / LLM Usage Transparency

This project was implemented with assistance from an LLM (ChatGPT) for:

- Overall architecture brainstorming and file structure.
- Writing boilerplate Dash / Plotly / pandas code.
- Implementing OLS, ADF and rolling correlation using `statsmodels` and `pandas`.
- Drafting this README and comments to clearly document the design.

All logic and flows were reviewed and lightly adapted to keep the demo **simple, single‑file runnable** and aligned with the assignment requirements.


