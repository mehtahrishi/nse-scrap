# 📈 NSE Live Market Terminal Guide

This guide explains how to:

* Download the full NSE stock list
* Inspect live stock JSON using curl
* Build a Python live market table
* Install dependencies

Data source: **National Stock Exchange of India**

---

## 🧾 1️⃣ Download Full NSE Stock List

This is the official NSE equity list.

```bash
curl -L "https://archives.nseindia.com/content/equities/EQUITY_L.csv" -o NSE_EQUITY_L.csv
```

Check file:

```bash
head NSE_EQUITY_L.csv
```

Columns include:

| Column          | Meaning             |
| --------------- | ------------------- |
| SYMBOL          | NSE ticker symbol   |
| NAME OF COMPANY | Company name        |
| SERIES          | EQ = Equity         |
| DATE OF LISTING | Listing date        |
| ISIN NUMBER     | Global security ID  |
| FACE VALUE      | Nominal share value |

---

## 🔍 2️⃣ Test Live Data for ONE Stock (Curl)

### Step 1 — Get NSE Cookies

```bash
curl -c cookies.txt -A "Mozilla/5.0" https://www.nseindia.com > /dev/null
```

### Step 2 — Fetch Stock JSON

```bash
curl -s -b cookies.txt \
  -A "Mozilla/5.0" \
  -H "Accept: application/json" \
  -H "Referer: https://www.nseindia.com/get-quotes/equity?symbol=RELIANCE" \
  "https://www.nseindia.com/api/quote-equity?symbol=RELIANCE" | jq
```

### Key Live Fields in Response

| Field      | JSON Path                         |
| ---------- | --------------------------------- |
| Price      | `priceInfo.lastPrice`             |
| Change     | `priceInfo.change`                |
| % Change   | `priceInfo.pChange`               |
| Open       | `priceInfo.open`                  |
| High       | `priceInfo.intraDayHighLow.max`   |
| Low        | `priceInfo.intraDayHighLow.min`   |
| Prev Close | `priceInfo.previousClose`         |
| Close      | `priceInfo.close`                 |
| VWAP       | `priceInfo.vwap`                  |
| Volume     | `preOpenMarket.totalTradedVolume` |

---

## 🐍 3️⃣ Python Live Market Table Script

Save as **`nse_live_table.py`**

```python
import requests
import pandas as pd
import time
from tabulate import tabulate
import os

csv_file = "NSE_EQUITY_L.csv"
df_static = pd.read_csv(csv_file)
df_static.columns = df_static.columns.str.strip().str.replace('\ufeff', '', regex=True)

df_static = df_static[[
    "SYMBOL",
    "NAME OF COMPANY",
    "SERIES",
    "DATE OF LISTING",
    "ISIN NUMBER",
    "FACE VALUE"
]]

session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
session.get("https://www.nseindia.com", headers=headers)

def fetch_live(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        r = session.get(url, headers=headers, timeout=5)
        data = r.json()

        price = data.get("priceInfo", {})
        intra = price.get("intraDayHighLow", {})
        preopen = data.get("preOpenMarket", {})

        return {
            "lastPrice": price.get("lastPrice"),
            "change": price.get("change"),
            "pChange": price.get("pChange"),
            "open": price.get("open"),
            "dayHigh": intra.get("max"),
            "dayLow": intra.get("min"),
            "prevClose": price.get("previousClose"),
            "close": price.get("close"),
            "vwap": price.get("vwap"),
            "volume": preopen.get("totalTradedVolume")
        }
    except:
        return None

def fmt(x):
    if isinstance(x, (int, float)):
        return f"{x:,.2f}"
    return "-" if x is None else x

batch_size = 20
start = 0

while True:
    batch = df_static.iloc[start:start+batch_size]
    table_rows = []

    for _, row in batch.iterrows():
        live = fetch_live(row["SYMBOL"])

        if live:
            combined = list(row.values) + [
                live["lastPrice"], live["change"], live["pChange"],
                live["open"], live["dayHigh"], live["dayLow"],
                live["prevClose"], live["close"], live["vwap"], live["volume"]
            ]
            table_rows.append(combined)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"📈 NSE LIVE MARKET TABLE (Stocks {start}–{start+batch_size})\n")

        headers_all = [
            "SYMBOL","NAME","SERIES","LISTED","ISIN","FACE",
            "PRICE","CHG","%CHG","OPEN","HIGH","LOW",
            "PREV CLOSE","CLOSE","VWAP","VOL"
        ]

        pretty_rows = []
        for r in table_rows:
            pretty_rows.append([
                r[0], r[1][:22], r[2], r[3], r[4], r[5],
                fmt(r[6]), fmt(r[7]), fmt(r[8]), fmt(r[9]),
                fmt(r[10]), fmt(r[11]), fmt(r[12]), fmt(r[13]),
                fmt(r[14]), fmt(r[15])
            ])

        print(tabulate(pretty_rows, headers=headers_all, tablefmt="fancy_grid", stralign="center"))
        time.sleep(3)

    start += batch_size
    if start >= len(df_static):
        start = 0

    print("⏳ Waiting before next batch...")
    time.sleep(60)
```

---

## 📦 4️⃣ requirements.txt

Create a file named **`requirements.txt`**

```
requests
pandas
tabulate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ 5️⃣ Run the Script

```bash
python nse_live_table.py
```

---

## ⚠️ Important Note

NSE endpoints are meant for website usage. Excessive automated requests may stop working.

This setup is best for **learning and experimentation**, not production trading systems.

---

If you'd like, next we can add:

📊 Sorting by gainers/losers
🎨 Color coding
💾 Auto-save CSV snapshots
