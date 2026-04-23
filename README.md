# FX Ichimoku MTF Scanner — Web Dashboard

Terminal-aesthetic web dashboard for 28 FX pairs.
Ichimoku Cloud MTF analysis · 4H Trend Strength · Auto-refresh every 2 min.
Deployable to **Vercel** (frontend + Python serverless API).

---

## Project Structure

```
fx-ichimoku-web/
├── api/
│   └── scan.py          ← Python serverless function (Vercel)
├── public/
│   └── index.html       ← Frontend (terminal UI)
├── requirements.txt     ← Python deps (yfinance, pandas, numpy)
├── vercel.json          ← Vercel routing config
└── README.md
```

---

## Deploy to Vercel (Free)

### Step 1 — Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2 — Login
```bash
vercel login
```

### Step 3 — Deploy from project root
```bash
cd fx-ichimoku-web
vercel --prod
```

Vercel will auto-detect the Python function in `/api/` and the static
site in `/public/`. The first deploy takes ~2 min to build.

Your app will be live at:  `https://your-project.vercel.app`

---

## Deploy to Netlify (Alternative — Frontend only)

> **Note:** Netlify does NOT support Python serverless functions natively.
> For Netlify you need a separate backend. See "Backend on Render" below.

### Frontend on Netlify
1. Go to [netlify.com](https://netlify.com) → New site → Deploy manually
2. Drag and drop the `public/` folder
3. Set environment variable `API_URL` to your backend URL (see below)
4. Done — frontend is live

### Backend on Render (Free Python server)
1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo (push this project first)
3. Build command: `pip install -r requirements.txt`
4. Start command: `python -m uvicorn api.render_server:app --host 0.0.0.0 --port $PORT`
5. Set environment: `PYTHON_VERSION = 3.11`

Then in `public/index.html`, change the API_URL constant:
```js
const API_URL = 'https://your-app.onrender.com/scan';
```

---

## Local Development

```bash
pip install yfinance pandas numpy

# Serve the frontend
cd public && python -m http.server 3000

# In another terminal, test the API directly
cd api && python -c "
import scan, json
from io import BytesIO

class FakeReq:
    path = '/api/scan?pair=EURUSD'

# Will print JSON result
"
```

Or install vercel CLI and run:
```bash
vercel dev
```
This spins up both the static files and the Python serverless function locally.

---

## Features

| Feature | Detail |
|---|---|
| **28 FX pairs** | Majors + crosses, no exotics |
| **5 timeframes** | W1 · D1 · H4 · H1 · M15 |
| **Ichimoku scoring** | Price vs Cloud · TK Cross · Future Cloud Color · Chikou-26 |
| **MTF weighted score** | W1(×5) D1(×4) H4(×3) H1(×2) M15(×1) |
| **4H Trend Strength** | Days in trend · cloud thickness · expanding/contracting |
| **Change detection** | Highlights pairs that flipped trend since last scan |
| **Auto-refresh** | Every 2 minutes, live countdown bar |
| **Terminal aesthetic** | Monospace font · dark green-on-black · CRT scanlines |
| **Fully responsive** | Works on mobile, tablet, desktop |
| **Filter + Sort** | All/Bull/Bear/Neutral · Strength/Most Bull/Most Bear |

---

## Scoring Reference

**Per TF (−4 to +4):**
1. Price vs Ichimoku Cloud ±1
2. Tenkan / Kijun Cross ±1
3. Future Cloud Color ±1
4. Chikou vs Price-26 ±1

**4H Strength Labels:**
- `STRONG`  = 5+ days in trend AND cloud expanding
- `GROWING` = 2+ days, stable or expanding
- `FADING`  = cloud contracting (momentum fading)
- `RANGING` = price inside cloud
- `WEAK`    = less than 1 day

---

## Notes

- Data source: **yfinance** (free, no API key needed)
- Vercel free tier: 100GB bandwidth, 100k function calls/month — plenty for personal use
- Scan takes ~90 sec server-side (28 pairs × 5 TF), results cached by the browser
- The Vercel function has a 60s timeout — if scan times out, reduce pairs in `scan.py`
