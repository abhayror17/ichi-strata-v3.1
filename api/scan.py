"""
FX Ichimoku MTF Scanner — Vercel Serverless API
GET /api/scan  →  returns full scan JSON for all 28 pairs
GET /api/scan?pair=EURUSD  →  single pair detail

All Ichimoku logic is identical to the CLI version.
Pivot points removed per request.
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    yf = None
    pd = None
    np = None

# ─────────────────────────────────────────────
FX_PAIRS = {
    "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
    "USDCHF": "USD/CHF", "AUDUSD": "AUD/USD", "NZDUSD": "NZD/USD",
    "USDCAD": "USD/CAD",
    "EURGBP": "EUR/GBP", "EURJPY": "EUR/JPY", "EURCHF": "EUR/CHF",
    "EURAUD": "EUR/AUD", "EURCAD": "EUR/CAD", "EURNZD": "EUR/NZD",
    "GBPJPY": "GBP/JPY", "GBPAUD": "GBP/AUD", "GBPCAD": "GBP/CAD",
    "GBPCHF": "GBP/CHF", "GBPNZD": "GBP/NZD",
    "AUDJPY": "AUD/JPY", "CADJPY": "CAD/JPY", "NZDJPY": "NZD/JPY",
    "CHFJPY": "CHF/JPY",
    "AUDCAD": "AUD/CAD", "AUDCHF": "AUD/CHF", "AUDNZD": "AUD/NZD",
    "CADCHF": "CAD/CHF", "NZDCAD": "NZD/CAD", "NZDCHF": "NZD/CHF",
}

TIMEFRAMES = {
    "W1":  {"interval": "1wk", "days": 730, "label": "Weekly", "weight": 5},
    "D1":  {"interval": "1d",  "days": 365, "label": "Daily",  "weight": 4},
    "H4":  {"interval": "1h",  "days": 90,  "label": "4H",     "weight": 3},
    "H1":  {"interval": "1h",  "days": 45,  "label": "1H",     "weight": 2},
    "M15": {"interval": "15m", "days": 8,   "label": "15M",    "weight": 1},
}

# ─────────────────────────────────────────────
def fetch_data(ticker, interval, days):
    try:
        now       = datetime.now(timezone.utc)
        start_str = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        end_str   = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        data = yf.download(ticker, start=start_str, end=end_str,
                           interval=interval, progress=False, auto_adjust=True)
        if data is None or data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.dropna(subset=["Close"])
        return data if len(data) >= 60 else None
    except Exception:
        return None


def resample_h4(df):
    if df is None or df.empty:
        return None
    try:
        df = df.copy()
        df.index = pd.to_datetime(df.index, utc=True)
        r = df.resample("4h", origin="epoch").agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum",
        }).dropna(subset=["Close"])
        return r if len(r) >= 60 else None
    except Exception:
        return None


def calc_ichimoku(df):
    high, low, close = df["High"], df["Low"], df["Close"]
    tenkan     = (high.rolling(9).max()  + low.rolling(9).min())  / 2
    kijun      = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a_raw = (tenkan + kijun) / 2
    span_b_raw = (high.rolling(52).max() + low.rolling(52).min()) / 2
    df = df.copy()
    df["tenkan"]        = tenkan
    df["kijun"]         = kijun
    df["cloud_span_a"]  = span_a_raw.shift(26)
    df["cloud_span_b"]  = span_b_raw.shift(26)
    df["future_span_a"] = span_a_raw
    df["future_span_b"] = span_b_raw
    df["price_26_ago"]  = close.shift(26)
    return df


def get_signal(df):
    if df is None or len(df) < 60:
        return None
    df  = calc_ichimoku(df)
    row = df.iloc[-1]
    try:
        price  = float(row["Close"])
        tenkan = float(row["tenkan"])
        kijun  = float(row["kijun"])
        ca     = float(row["cloud_span_a"])
        cb     = float(row["cloud_span_b"])
        if any(pd.isna(v) for v in [price, tenkan, kijun, ca, cb]):
            return None
        cloud_top = max(ca, cb)
        cloud_bot = min(ca, cb)
        pvc = 1 if price > cloud_top else (-1 if price < cloud_bot else 0)
        tkc = 1 if tenkan > kijun    else (-1 if tenkan < kijun    else 0)
        fa, fb = float(row["future_span_a"]), float(row["future_span_b"])
        fcc = 0 if (pd.isna(fa) or pd.isna(fb)) else (1 if fa>fb else (-1 if fa<fb else 0))
        p26 = float(row["price_26_ago"])
        chk = 0 if pd.isna(p26) else (1 if price>p26 else (-1 if price<p26 else 0))
        score = pvc + tkc + fcc + chk

        if   score >= 3: trend, short = "STRONG BULL", "▲▲"
        elif score == 2: trend, short = "BULL",        "▲"
        elif score == 1: trend, short = "WEAK BULL",   "△"
        elif score == 0: trend, short = "NEUTRAL",     "—"
        elif score ==-1: trend, short = "WEAK BEAR",   "▽"
        elif score ==-2: trend, short = "BEAR",        "▼"
        else:            trend, short = "STRONG BEAR", "▼▼"

        return {
            "score": score, "trend": trend, "short": short,
            "price": round(price, 5),
            "conditions": {"pvc": pvc, "tkc": tkc, "fcc": fcc, "chk": chk},
        }
    except Exception:
        return None


def calc_h4_strength(h4_df, symbol):
    if h4_df is None or len(h4_df) < 80:
        return None
    try:
        df    = calc_ichimoku(h4_df.copy())
        valid = df.dropna(subset=["cloud_span_a", "cloud_span_b"])
        if len(valid) < 10:
            return None

        close_v     = valid["Close"]
        cloud_top_v = valid[["cloud_span_a", "cloud_span_b"]].max(axis=1)
        cloud_bot_v = valid[["cloud_span_a", "cloud_span_b"]].min(axis=1)

        latest_price = float(close_v.iloc[-1])
        ct_now       = float(cloud_top_v.iloc[-1])
        cb_now       = float(cloud_bot_v.iloc[-1])

        if latest_price > ct_now:   side = "bull"
        elif latest_price < cb_now: side = "bear"
        else:                       side = "inside"

        streak = 0
        for i in range(len(valid) - 1, -1, -1):
            p  = float(close_v.iloc[i])
            ct = float(cloud_top_v.iloc[i])
            cb = float(cloud_bot_v.iloc[i])
            if   side == "bull"   and p > ct:  streak += 1
            elif side == "bear"   and p < cb:  streak += 1
            elif side == "inside" and cb<=p<=ct: streak += 1
            else: break

        streak_days  = round(streak * 4 / 24, 1)
        thick_now    = float(ct_now - cb_now)
        pip_mult     = 100.0 if "JPY" in symbol else 10000.0
        thick_pips   = round(thick_now * pip_mult, 1)

        lb = 10
        prev_thick = (cloud_top_v.iloc[-(lb+1):-1] - cloud_bot_v.iloc[-(lb+1):-1]).mean() \
                     if len(valid) > lb+1 else thick_now
        chg_pct = (thick_now - prev_thick) / prev_thick * 100 if prev_thick > 0 else 0.0

        if   chg_pct >  3.0: momentum, icon = "expanding",   "↑"
        elif chg_pct < -3.0: momentum, icon = "contracting", "↓"
        else:                 momentum, icon = "stable",      "→"

        if   streak_days >= 5 and momentum == "expanding":   label = "STRONG"
        elif streak_days >= 2 and momentum in ("expanding","stable"): label = "GROWING"
        elif streak_days >= 1 and momentum == "contracting": label = "FADING"
        elif side == "inside":                               label = "RANGING"
        else:                                                label = "WEAK"

        return {
            "side": side, "streak_days": streak_days,
            "thick_pips": thick_pips, "momentum": momentum,
            "momentum_icon": icon, "change_pct": round(chg_pct, 1),
            "label": label,
        }
    except Exception:
        return None


def analyze_pair(symbol):
    ticker = symbol + "=X"
    result = {"symbol": symbol, "name": FX_PAIRS.get(symbol, symbol)}
    tf_signals = {}
    mtf_score = mtf_weight = 0
    price = None

    h1_raw = fetch_data(ticker, "1h", 90)

    for tf_key, tf_cfg in TIMEFRAMES.items():
        if tf_key == "H4":
            df = resample_h4(h1_raw)
        elif tf_key == "H1":
            if h1_raw is not None:
                try:
                    idx = pd.to_datetime(h1_raw.index, utc=True)
                    cut = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=45)
                    mask = idx >= cut
                    df = h1_raw[mask.values] if mask.sum() >= 60 else h1_raw
                except Exception:
                    df = h1_raw
            else:
                df = None
        elif tf_key == "M15":
            df = fetch_data(ticker, "15m", 8)
        else:
            df = fetch_data(ticker, tf_cfg["interval"], tf_cfg["days"])

        sig = get_signal(df)
        tf_signals[tf_key] = sig
        if sig:
            mtf_score  += sig["score"] * tf_cfg["weight"]
            mtf_weight += tf_cfg["weight"]

    for tf in ["M15", "H1", "H4", "D1", "W1"]:
        if tf_signals.get(tf):
            price = tf_signals[tf]["price"]
            break

    result["tf_signals"] = tf_signals
    result["price"]      = price

    if mtf_weight > 0:
        norm = mtf_score / mtf_weight
        result["mtf_score"] = round(norm, 2)
        if   norm >= 3.5: result["mtf_trend"] = "STRONG BULL"
        elif norm >= 2.0: result["mtf_trend"] = "BULL"
        elif norm >= 0.5: result["mtf_trend"] = "WEAK BULL"
        elif norm > -0.5: result["mtf_trend"] = "NEUTRAL"
        elif norm > -2.0: result["mtf_trend"] = "WEAK BEAR"
        elif norm > -3.5: result["mtf_trend"] = "BEAR"
        else:             result["mtf_trend"] = "STRONG BEAR"
    else:
        result["mtf_score"] = 0.0
        result["mtf_trend"] = "NO DATA"

    h4_df = resample_h4(h1_raw)
    result["h4_strength"] = calc_h4_strength(h4_df, symbol)

    return result


# ─────────────────────────────────────────────
#  Vercel handler
# ─────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        pair   = params.get("pair", [None])[0]

        if yf is None:
            self._respond(500, {"error": "yfinance not installed"})
            return

        try:
            if pair:
                sym = pair.upper().replace("/", "")
                if sym not in FX_PAIRS:
                    self._respond(400, {"error": f"Unknown pair: {sym}"})
                    return
                data = analyze_pair(sym)
            else:
                results = []
                for sym in FX_PAIRS:
                    r = analyze_pair(sym)
                    r["symbol"] = sym
                    results.append(r)
                results.sort(key=lambda x: abs(x.get("mtf_score", 0)), reverse=True)
                data = {
                    "pairs": results,
                    "scanned_at": datetime.now(timezone.utc).isoformat(),
                    "count": len(results),
                }
            self._respond(200, data)
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status, payload):
        body = json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
