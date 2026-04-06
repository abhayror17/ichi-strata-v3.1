# Ichi-Strata v3.1 - Ichimoku + Pivot Points Scanner

A multi-timeframe trading scanner combining Ichimoku Cloud system with Pivot Points for identifying high-probability trade setups.

## Strategy Logic

### Step 1: Daily Timeframe Analysis
- Checks if **Tenkan, Kijun, and Chikou** (3 lines) are all above or below the cloud
- Checks if price is above or below the Daily Pivot
- Determines Daily market direction: **BUYERS** or **SELLERS** Market

### Step 2: Current Timeframe Analysis (15M recommended)
- Same 3-line + pivot check on current timeframe
- Determines current TF market direction

### Step 3: Signal Generation
| Daily | Current TF | Signal |
|-------|------------|--------|
| Buyers Market | Buyers Market | **BUY** |
| Sellers Market | Sellers Market | **SELL** |
| Mixed | - | **WAIT** |

---

## Signal Conditions

### BUY Signal Conditions
All must be true on BOTH Daily AND Current TF:
1. Tenkan-sen (Blue) > Cloud Top
2. Kijun-sen (Red) > Cloud Top
3. Chikou Span > Cloud Top
4. Price > Pivot

### SELL Signal Conditions
All must be true on BOTH Daily AND Current TF:
1. Tenkan-sen (Blue) < Cloud Bottom
2. Kijun-sen (Red) < Cloud Bottom
3. Chikou Span < Cloud Bottom
4. Price < Pivot

---

## Features

| Feature | Description |
|---------|-------------|
| **Info Table** | Real-time status of all conditions for Daily & Current TF |
| **Signal Labels** | Visual BUY/SELL labels with current SL price |
| **Cloud Visualization** | Green cloud = bullish, Red cloud = bearish |
| **Pivot Lines** | P, R1, R2, S1, S2 displayed on chart |
| **Stop Loss** | Auto-tracked via Kijun-sen (Red Base Line) |
| **Alerts** | Built-in alert conditions for signals |
| **Background Color** | Green/Red highlight when signal is active |
| **Pivot Types** | Traditional, Fibonacci, Woodie, Classic, DM, Camarilla |

---

## Ichimoku Lines Reference

| Line | Color | Period | Purpose |
|------|-------|--------|---------|
| Tenkan-sen | Blue | 9 | Conversion line - follows price |
| Kijun-sen | Red | 26 | Base line - **Stop Loss** |
| Chikou Span | Green | Close shifted -26 | Lagging span |
| Senkou A/B | Cloud | 26/52 | Future cloud support/resistance |

---

## Installation

1. Open TradingView
2. Go to Pine Editor
3. Copy the contents of `ichimoku_pivot_scanner.pine`
4. Paste into editor and click "Add to Chart"

---

## Recommended Usage

1. Apply indicator on **15-minute timeframe**
2. Wait for both Daily and 15M to align
3. Enter on signal label appearance
4. Set SL at **Kijun-sen (Red line)** - it updates dynamically

---

## Settings

### Ichimoku Settings
- **Conversion Line Length (Tenkan)**: 9 (default)
- **Base Line Length (Kijun)**: 26 (default)
- **Leading Span B Length**: 52 (default)
- **Displacement**: 26 (default)

### Pivot Point Settings
- **Pivot Type**: Traditional, Fibonacci, Woodie, Classic, DM, Camarilla

### Display Settings
- Show/hide Signal Labels
- Show/hide Info Table
- Show/hide Ichimoku Cloud
- Show/hide Pivot Lines

### Alert Settings
- Enable/disable Buy Signal Alerts
- Enable/disable Sell Signal Alerts

---

## Risk Management

- **Stop Loss**: Kijun-sen (Red Base Line) - automatically tracks with price
- Always wait for both timeframes to align before entering
- Works on Forex, Metals, Crypto, and other instruments

---

## License

MIT License - Use at your own risk.

---

## Author

Created for multi-timeframe analysis using Ichimoku Cloud and Pivot Points.
