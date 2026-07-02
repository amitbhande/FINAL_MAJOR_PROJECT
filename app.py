import io
import time
from typing import List, Optional

import dash
from dash import Dash, Input, Output, State, dcc, html
import numpy as np
import pandas as pd
import plotly.graph_objs as go

from analytics_engine import AnalyticsEngine
from binance_ingestor import BinanceIngestor
from data_store import DataStore


DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
TIMEFRAMES = {
    "1s": "1S",
    "1m": "1T",
    "5m": "5T",
}


store = DataStore()
engine = AnalyticsEngine()
ingestor = BinanceIngestor(store, DEFAULT_SYMBOLS)
ingestor.start()


app: Dash = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server


def layout() -> html.Div:
    return html.Div(
        style={"fontFamily": "Arial", "margin": "0 2rem"},
        children=[
            html.H2("Pairs Trading Demo – Binance Live Ticks"),
            html.Div(
                style={"display": "flex", "gap": "1rem"},
                children=[
                    html.Div(
                        style={"flex": 1},
                        children=[
                            html.Label("Symbol X"),
                            dcc.Dropdown(
                                id="symbol-x",
                                options=[{"label": s, "value": s} for s in DEFAULT_SYMBOLS],
                                value=DEFAULT_SYMBOLS[0],
                                clearable=False,
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": 1},
                        children=[
                            html.Label("Symbol Y"),
                            dcc.Dropdown(
                                id="symbol-y",
                                options=[{"label": s, "value": s} for s in DEFAULT_SYMBOLS[1:]],
                                value=DEFAULT_SYMBOLS[1],
                                clearable=False,
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": 1},
                        children=[
                            html.Label("Timeframe"),
                            dcc.Dropdown(
                                id="timeframe",
                                options=[{"label": k, "value": v} for k, v in TIMEFRAMES.items()],
                                value="1T",
                                clearable=False,
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": 1},
                        children=[
                            html.Label("Rolling Window (points)"),
                            dcc.Input(
                                id="rolling-window",
                                type="number",
                                min=20,
                                max=2000,
                                step=10,
                                value=100,
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": 1},
                        children=[
                            html.Label("Z-Score Alert Threshold"),
                            dcc.Input(
                                id="z-threshold",
                                type="number",
                                value=2.0,
                                step=0.25,
                            ),
                        ],
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                style={"display": "flex", "gap": "1rem"},
                children=[
                    html.Button("Run ADF Test", id="run-adf", n_clicks=0),
                    html.Div(id="adf-result", style={"alignSelf": "center"}),
                    html.Div(id="alert-banner", style={"color": "red", "fontWeight": "bold"}),
                ],
            ),
            html.Br(),
            html.H4("Live Prices, Spread & Z-Score"),
            dcc.Graph(id="price-spread-fig"),
            dcc.Graph(id="zscore-fig"),
            html.Button("Download current analytics CSV", id="btn-download"),
            html.Hr(),
            html.H4("Rolling Correlation"),
            dcc.Graph(id="corr-fig"),
            html.Hr(),
            html.H4("Uploaded OHLC Analytics"),
            dcc.Upload(
                id="upload-ohlc",
                children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px 0",
                },
                multiple=False,
            ),
            html.Div(id="upload-status"),
            dcc.Graph(id="upload-price-fig"),
            dcc.Graph(id="upload-zscore-fig"),
            html.Button(
                "Download uploaded analytics CSV", id="btn-download-uploaded"
            ),
            dcc.Interval(id="refresh-interval", interval=1000, n_intervals=0),
            dcc.Store(id="last-zscore"),
            dcc.Store(id="uploaded-ohlc"),
            dcc.Download(id="download-data"),
            dcc.Download(id="download-uploaded"),
        ],
    )


app.layout = layout


def _load_and_resample(symbol: str, timeframe: str) -> pd.DataFrame:
    df = store.get_ticks_df(symbol, lookback_seconds=3600)
    if df.empty:
        return df
    return engine.resample_ticks(df, timeframe)


def _build_price_spread_fig(
    tf: str,
    sym_x: str,
    sym_y: str,
    df_x: pd.DataFrame,
    df_y: pd.DataFrame,
    analytics,
) -> go.Figure:
    fig = go.Figure()
    if not df_x.empty:
        fig.add_trace(
            go.Scatter(
                x=df_x.index,
                y=df_x["close"],
                mode="lines",
                name=f"{sym_x} close",
            )
        )
    if not df_y.empty:
        fig.add_trace(
            go.Scatter(
                x=df_y.index,
                y=df_y["close"],
                mode="lines",
                name=f"{sym_y} close",
            )
        )
    if analytics:
        spread = analytics.spread_series
        fig.add_trace(
            go.Scatter(
                x=spread.index,
                y=spread.values,
                mode="lines",
                name="Spread (Y - beta X)",
                yaxis="y2",
            )
        )

    fig.update_layout(
        title=f"Prices and Spread ({tf})",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Price"),
        yaxis2=dict(
            title="Spread",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        hovermode="x unified",
    )
    return fig


def _build_zscore_fig(analytics) -> go.Figure:
    fig = go.Figure()
    if analytics:
        z = analytics.zscore_series
        fig.add_trace(
            go.Scatter(
                x=z.index,
                y=z.values,
                mode="lines",
                name="Z-Score",
            )
        )
        fig.add_hline(y=2, line_dash="dash", line_color="red")
        fig.add_hline(y=-2, line_dash="dash", line_color="red")

    fig.update_layout(
        title="Z-Score of Spread",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Z-Score"),
        hovermode="x unified",
    )
    return fig


def _build_corr_fig(analytics) -> go.Figure:
    fig = go.Figure()
    if analytics and analytics.rolling_corr is not None:
        rc = analytics.rolling_corr
        fig.add_trace(
            go.Scatter(
                x=rc.index,
                y=rc.values,
                mode="lines",
                name="Rolling Correlation",
            )
        )
    fig.update_layout(
        title="Rolling Correlation of Log Returns",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Correlation"),
        hovermode="x unified",
    )
    return fig


@app.callback(
    Output("price-spread-fig", "figure"),
    Output("zscore-fig", "figure"),
    Output("corr-fig", "figure"),
    Output("last-zscore", "data"),
    Input("refresh-interval", "n_intervals"),
    State("symbol-x", "value"),
    State("symbol-y", "value"),
    State("timeframe", "value"),
    State("rolling-window", "value"),
    prevent_initial_call=False,
)
def update_live_graphs(
    _: int,
    sym_x: str,
    sym_y: str,
    timeframe: str,
    window: int,
):
    df_x = _load_and_resample(sym_x, timeframe)
    df_y = _load_and_resample(sym_y, timeframe)
    analytics = engine.compute_pair_analytics(df_x, df_y, window=window)

    price_spread_fig = _build_price_spread_fig(
        timeframe, sym_x, sym_y, df_x, df_y, analytics
    )
    zscore_fig = _build_zscore_fig(analytics)
    corr_fig = _build_corr_fig(analytics)

    last_z = None
    if analytics and not analytics.zscore_series.dropna().empty:
        last_z = float(analytics.zscore_series.dropna().iloc[-1])

    return price_spread_fig, zscore_fig, corr_fig, last_z


@app.callback(
    Output("alert-banner", "children"),
    Input("last-zscore", "data"),
    State("z-threshold", "value"),
)
def update_alert(z: Optional[float], threshold: float):
    if z is None or threshold is None:
        return ""
    if abs(z) >= threshold:
        direction = "short" if z > 0 else "long"
        return f"ALERT: |z|={z:.2f} >= {threshold:.2f} – consider {direction} spread trade."
    return ""


@app.callback(
    Output("adf-result", "children"),
    Input("run-adf", "n_clicks"),
    State("symbol-x", "value"),
    State("symbol-y", "value"),
    State("timeframe", "value"),
    State("rolling-window", "value"),
    prevent_initial_call=True,
)
def run_adf(n_clicks, sym_x, sym_y, timeframe, window):
    if n_clicks is None or n_clicks == 0:
        return ""
    df_x = _load_and_resample(sym_x, timeframe)
    df_y = _load_and_resample(sym_y, timeframe)
    analytics = engine.compute_pair_analytics(df_x, df_y, window=window)
    if not analytics or analytics.adf_pvalue is None:
        return "ADF: insufficient data."
    return f"ADF p-value on spread: {analytics.adf_pvalue:.4f}"


@app.callback(
    Output("download-data", "data"),
    Input("btn-download", "n_clicks"),
    State("symbol-x", "value"),
    State("symbol-y", "value"),
    State("timeframe", "value"),
    State("rolling-window", "value"),
    prevent_initial_call=True,
)
def download_current(n_clicks, sym_x, sym_y, timeframe, window):
    if not n_clicks:
        return dash.no_update

    df_x = _load_and_resample(sym_x, timeframe)
    df_y = _load_and_resample(sym_y, timeframe)
    analytics = engine.compute_pair_analytics(df_x, df_y, window=window)
    if not analytics:
        return dash.no_update

    df_out = pd.DataFrame(
        {
            "spread": analytics.spread_series,
            "zscore": analytics.zscore_series,
        }
    )
    buf = io.StringIO()
    df_out.to_csv(buf)
    buf.seek(0)
    return dict(content=buf.getvalue(), filename="pair_analytics.csv")


def _parse_contents(contents: str) -> Optional[pd.DataFrame]:
    import base64

    parts = contents.split(",")
    if len(parts) != 2:
        return None
    decoded = base64.b64decode(parts[1])
    df = pd.read_csv(io.BytesIO(decoded))
    # Expect at least: timestamp, close
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df.set_index("timestamp", inplace=True)
    elif "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df.set_index("time", inplace=True)
    return df


@app.callback(
    Output("uploaded-ohlc", "data"),
    Output("upload-status", "children"),
    Input("upload-ohlc", "contents"),
    State("upload-ohlc", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
    if contents is None:
        return dash.no_update, ""
    df = _parse_contents(contents)
    if df is None or "close" not in df.columns:
        return None, "Upload failed: expected columns including 'timestamp'/'time' and 'close'."
    # For simplicity we only use single series; treat as X, synthetic Y with small noise
    return df.to_json(date_unit="ns"), f"Uploaded {filename} with {len(df)} rows."


@app.callback(
    Output("upload-price-fig", "figure"),
    Output("upload-zscore-fig", "figure"),
    Input("uploaded-ohlc", "data"),
)
def update_upload_figs(data_json):
    fig_price = go.Figure()
    fig_z = go.Figure()
    if not data_json:
        fig_price.update_layout(title="No upload yet")
        fig_z.update_layout(title="No upload yet")
        return fig_price, fig_z

    df = pd.read_json(data_json)
    df.index = pd.to_datetime(df.index)
    fig_price.add_trace(
        go.Scatter(x=df.index, y=df["close"], mode="lines", name="Close"),
    )
    fig_price.update_layout(
        title="Uploaded OHLC – Close",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Price"),
    )

    # Simple z-score on uploaded close series
    spread = df["close"]
    z = (spread - spread.rolling(50).mean()) / spread.rolling(50).std()
    fig_z.add_trace(
        go.Scatter(x=z.index, y=z.values, mode="lines", name="Z-Score"),
    )
    fig_z.update_layout(
        title="Uploaded Close – Z-Score (window=50)",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Z-Score"),
    )
    return fig_price, fig_z


@app.callback(
    Output("download-uploaded", "data"),
    Input("btn-download-uploaded", "n_clicks"),
    State("uploaded-ohlc", "data"),
    prevent_initial_call=True,
)
def download_uploaded(n_clicks, data_json):
    if not n_clicks or not data_json:
        return dash.no_update
    df = pd.read_json(data_json)
    df.index = pd.to_datetime(df.index)
    spread = df["close"]
    z = (spread - spread.rolling(50).mean()) / spread.rolling(50).std()
    df_out = pd.DataFrame({"close": df["close"], "zscore": z})
    buf = io.StringIO()
    df_out.to_csv(buf)
    buf.seek(0)
    return dict(content=buf.getvalue(), filename="uploaded_analytics.csv")


if __name__ == "__main__":
    app.run_server(debug=True)


