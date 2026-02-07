# 1 then 2 then 3 
import requests
import pandas as pd
import time
import os
import shutil

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
        week = price.get("weekHighLow", {})
        preopen = data.get("preOpenMarket", {})
        info = data.get("info", {})
        meta = data.get("metadata", {})
        sec = data.get("securityInfo", {})
        industry = data.get("industryInfo", {})

        last = price.get("lastPrice")
        vwap = price.get("vwap")

        return {
            "lastPrice": last,
            "change": price.get("change"),
            "pChange": price.get("pChange"),
            "open": price.get("open"),
            "dayHigh": intra.get("max"),
            "dayLow": intra.get("min"),
            "prevClose": price.get("previousClose"),
            "close": price.get("close"),
            "vwap": vwap,
            "volume": preopen.get("totalTradedVolume"),

            "upperCP": price.get("upperCP"),
            "lowerCP": price.get("lowerCP"),
            "priceBand": price.get("pPriceBand"),
            "wHigh": week.get("max"),
            "wLow": week.get("min"),
            "vwapDiff": ((last - vwap) / vwap * 100) if last and vwap else None,
            "buyQty": preopen.get("totalBuyQuantity"),
            "sellQty": preopen.get("totalSellQuantity"),
            "imbalance": (preopen.get("totalBuyQuantity", 0) - preopen.get("totalSellQuantity", 0)),
            "sector": industry.get("sector"),
            "industry": industry.get("industry"),
            "fno": info.get("isFNOSec"),
            "index": meta.get("pdSectorInd"),
            "status": sec.get("tradingStatus"),
        }
    except:
        return None


def fmt(x):
    if isinstance(x, (int, float)):
        return f"{x:,.2f}"
    return "-" if x is None else str(x)


HEADERS = [
    "SYMBOL","NAME","SER","LISTED","ISIN","FACE",
    "PRICE","CHG","%CHG","OPEN","HIGH","LOW","VWAP","VWAP%",
    "UPPER","LOWER","BAND","52W HIGH","52W LOW",
    "BUY QTY","SELL QTY","IMBAL",
    "SECTOR","INDUSTRY","F&O","INDEX","STATUS","VOL"
]

BASE_WIDTHS = [
    8,24,3,10,12,5,
    10,9,7,10,10,10,10,7,
    8,8,10,10,10,
    10,10,8,
    14,16,4,12,10,10
]

NAME_MIN = 6
NAME_MAX = 60
LEFT_ALIGN_IDX = {0,1,2,3,4,5,22,23,25,26}


def term_width(default=160):
    return shutil.get_terminal_size(fallback=(default, 24)).columns


def ellipsize(s, width):
    s = "-" if s is None else str(s)
    return s if len(s) <= width else s[:width-1] + "…"


def compute_widths():
    widths = BASE_WIDTHS[:]
    spare = term_width() - (sum(widths) + len(widths)-1)
    if spare > 0:
        widths[1] = min(NAME_MAX, widths[1] + spare)
    return widths


def format_row(cells, widths):
    out = []
    for i, cell in enumerate(cells):
        w = widths[i]
        text = ellipsize(cell, w)
        if i in LEFT_ALIGN_IDX:
            out.append(text.ljust(w))
        else:
            out.append(text.rjust(w))
    return " ".join(out)


batch_size = 10
start = 0

while True:
    batch = df_static.iloc[start:start+batch_size]
    rows = []

    for _, row in batch.iterrows():
        live = fetch_live(row["SYMBOL"])
        if live:
            rows.append([
                row["SYMBOL"], row["NAME OF COMPANY"], row["SERIES"],
                row["DATE OF LISTING"], row["ISIN NUMBER"], row["FACE VALUE"],
                fmt(live["lastPrice"]), fmt(live["change"]), fmt(live["pChange"]),
                fmt(live["open"]), fmt(live["dayHigh"]), fmt(live["dayLow"]),
                fmt(live["vwap"]), fmt(live["vwapDiff"]),
                fmt(live["upperCP"]), fmt(live["lowerCP"]), live["priceBand"],
                fmt(live["wHigh"]), fmt(live["wLow"]),
                fmt(live["buyQty"]), fmt(live["sellQty"]), fmt(live["imbalance"]),
                live["sector"], live["industry"], str(live["fno"]),
                live["index"], live["status"], fmt(live["volume"])
            ])

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"📈 NSE LIVE MARKET TABLE (Stocks {start}-{start+batch_size})\n")

        widths = compute_widths()
        header_line = format_row(HEADERS, widths)
        print(header_line)
        print("-"*len(header_line))

        for r in rows:
            print(format_row(r, widths))

        time.sleep(3)

    start += batch_size
    if start >= len(df_static):
        start = 0

    print("\n⏳ Waiting before next batch...")
    time.sleep(30)
