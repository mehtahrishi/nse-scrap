import requests
import pandas as pd
import time
import os
import shutil

csv_file = "NSE_EQUITY_L.csv"
df_static = pd.read_csv(csv_file)

# Normalize columns
df_static.columns = df_static.columns.str.strip().str.replace('\ufeff', '', regex=True)

# Removed PAID UP VALUE and MARKET LOT
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
    except Exception:
        return None


def fmt(x):
    if isinstance(x, (int, float)):
        return f"{x:,.2f}"
    return "-" if x is None else str(x)


# -------- Invisible table helpers (column aligned, no borders) --------

HEADERS = [
    "SYMBOL", "NAME", "SERIES", "LISTED", "ISIN", "FACE",
    "PRICE", "CHG", "%CHG", "OPEN", "HIGH", "LOW",
    "PREV CLOSE", "CLOSE", "VWAP", "VOL"
]

# Fixed base widths for all columns except NAME, which will flex
BASE_WIDTHS = [
    8,   # SYMBOL
    24,  # NAME (starting width; may shrink/grow)
    3,   # SERIES
    10,  # LISTED
    12,  # ISIN
    5,   # FACE
    10,  # PRICE
    9,   # CHG
    7,   # %CHG
    10,  # OPEN
    10,  # HIGH
    10,  # LOW
    12,  # PREV CLOSE
    10,  # CLOSE
    10,  # VWAP
    10,  # VOL
]

# Minimum width only applies to NAME; others are fixed and must not truncate
NAME_MIN = 6
NAME_MAX = 60

# Alignment: left for text columns, right for numeric-like columns
LEFT_ALIGN_IDX = {0, 1, 2, 3, 4, 5}


def term_width(default=120):
    try:
        return shutil.get_terminal_size(fallback=(default, 24)).columns
    except Exception:
        return default


def ellipsize(s: str, width: int, side: str = 'right') -> str:
    s = "-" if s is None else str(s)
    if width is None:
        return s
    if width <= 0:
        return ""
    if len(s) <= width:
        return s
    if width == 1:
        return "…"
    if side == 'right':
        return s[: max(1, width - 1)] + "…"
    return "…" + s[-(width - 1):]


def compute_widths_fixed_except_name(headers, base_widths, name_min=NAME_MIN, name_max=NAME_MAX):
    widths = base_widths[:]
    n = len(headers)

    # Ensure header labels fit in their columns; if a label is longer than its base (except NAME),
    # we let it overflow into NAME by expanding NAME first; otherwise we keep fixed.
    for i, h in enumerate(headers):
        if i == 1:
            widths[i] = max(widths[i], len(str(h)), name_min)
        else:
            widths[i] = max(widths[i], len(str(h)))

    def total_len(ws):
        # Invisible table: sum of widths + 1 space between columns
        return sum(ws) + (n - 1)

    tw = term_width()

    # Grow NAME to use spare space up to name_max
    spare = tw - total_len(widths)
    if spare > 0:
        grow = min(spare, max(0, name_max - widths[1]))
        widths[1] += grow

    # If overflow, only shrink NAME down to name_min; others remain fixed
    overflow = total_len(widths) - tw
    if overflow > 0 and widths[1] > name_min:
        shrink = min(overflow, widths[1] - name_min)
        widths[1] -= shrink
        overflow -= shrink

    # If still overflow > 0, we cannot shrink other columns by requirement; it will overflow terminal
    # but we keep all non-NAME columns intact and only NAME fully minimized.
    return widths


def format_row(cells, widths):
    out = []
    for i, cell in enumerate(cells):
        w = widths[i]
        if i == 1:
            # NAME is the only column that may be truncated (right-side ellipsis)
            clipped = ellipsize(cell, w, side='right')
            out.append(clipped.ljust(w))
        else:
            text = str(cell)
            # Do not truncate non-NAME columns; pad to width and let line wrap if user terminal too small
            if i in LEFT_ALIGN_IDX:
                out.append(text.ljust(w)[:w])
            else:
                out.append(text.rjust(w)[-w:])
    return " ".join(out)


batch_size = 20
start = 0

while True:
    batch = df_static.iloc[start:start + batch_size]
    table_rows = []

    for _, row in batch.iterrows():
        symbol = row["SYMBOL"]
        live = fetch_live(symbol)

        if live:
            combined = list(row.values) + [
                live["lastPrice"],
                live["change"],
                live["pChange"],
                live["open"],
                live["dayHigh"],
                live["dayLow"],
                live["prevClose"],
                live["close"],
                live["vwap"],
                live["volume"]
            ]
            table_rows.append(combined)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"📈 NSE LIVE MARKET TABLE (Stocks {start}–{start + batch_size})\n")

        # Build raw rows with formatted numbers
        raw_rows = []
        for r in table_rows:
            raw_rows.append([
                str(r[0]),          # SYMBOL
                str(r[1]),          # NAME
                str(r[2]),          # SERIES
                str(r[3]),          # DATE OF LISTING
                str(r[4]),          # ISIN
                str(r[5]),          # FACE VALUE
                fmt(r[6]),          # PRICE
                fmt(r[7]),          # CHANGE
                fmt(r[8]),          # %CHANGE
                fmt(r[9]),          # OPEN
                fmt(r[10]),         # HIGH
                fmt(r[11]),         # LOW
                fmt(r[12]),         # PREV CLOSE
                fmt(r[13]),         # CLOSE
                fmt(r[14]),         # VWAP
                fmt(r[15])          # VOL
            ])

        widths = compute_widths_fixed_except_name(HEADERS, BASE_WIDTHS, name_min=NAME_MIN, name_max=NAME_MAX)

        # Header
        header_line = format_row(HEADERS, widths)
        print(header_line)
        print("-" * len(header_line))

        # Rows
        for rv in raw_rows:
            print(format_row(rv, widths))

        print("\nUpdating next stock...\n")

        time.sleep(3)

    start += batch_size
    if start >= len(df_static):
        start = 0

    print("⏳ Waiting before next batch...")
    time.sleep(60)
