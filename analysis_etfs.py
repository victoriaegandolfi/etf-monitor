import yfinance as yf
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np

# ===============================
# CONFIG
# ===============================

ETFS = [
    "IVV", "VUG", "QQQ", "SCHD",
    "XLK", "IYW", "MAGS"
]

DATA_DIR = Path("data/etfs")
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOOKBACK_DAYS = 500
MM_WINDOW = 252

# ===============================
# FUNÇÕES
# ===============================

def get_signal(price, mm, dist_topo):
    if price < mm * 0.9 and dist_topo < -20:
        return "COMPRAR"
    if price > mm * 1.1 or dist_topo > -5:
        return "REDUZIR"
    return "NEUTRO"

# ===============================
# PROCESSAMENTO
# ===============================

summary_rows = []
signal_rows = []

for etf in ETFS:
    print(f"Processando {etf}")

    df = yf.download(
        etf,
        period=f"{LOOKBACK_DAYS}d",
        progress=False
    )

    if df.empty:
        print(f"⚠️ Sem dados para {etf}")
        continue

    df = df.reset_index()
    df["Close"] = df["Close"].astype(float)

    # Média móvel 1 ano
    df["MM_1Y"] = df["Close"].rolling(MM_WINDOW).mean()

    # Topo 12 meses
    df["Topo_12m"] = df["Close"].rolling(MM_WINDOW).max()

    latest = df.iloc[-1]

    price = latest["Close"]
    mm = latest["MM_1Y"]
    topo = latest["Topo_12m"]

    dist_mm = (price / mm - 1) * 100
    dist_topo = (price / topo - 1) * 100

    signal = get_signal(price, mm, dist_topo)

    # ===============================
    # SUMMARY
    # ===============================

    retorno_12m = (
        df["Close"].iloc[-1] /
        df["Close"].iloc[-MM_WINDOW] - 1
    ) * 100

    summary_rows.append({
        "ETF": etf,
        "Preço Atual": round(price, 2),
        "Média 1 Ano": round(mm, 2),
        "Desvio MM (%)": round(dist_mm, 2),
        "Retorno 12m (%)": round(retorno_12m, 2)
    })

    signal_rows.append({
        "ETF": etf,
        "Sinal": signal,
        "Distância do topo (%)": round(dist_topo, 2)
    })

    # ===============================
    # HISTÓRICO NORMALIZADO
    # ===============================

    hist = df[["Date", "Close"]].copy()
    hist["price_norm"] = hist["Close"] / hist["Close"].iloc[0] * 100

    hist.rename(
        columns={"Date": "date"},
        inplace=True
    )

    hist[["date", "price_norm"]].to_json(
        DATA_DIR / f"{etf}_history.json",
        orient="records",
        date_format="iso"
    )

# ===============================
# DASHBOARD JSON
# ===============================

dashboard = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "ipca_12m": None,  # opcional depois
    "summary": summary_rows,
    "signals": signal_rows
}

with open(DATA_DIR / "dashboard_etfs.json", "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

print("✅ dashboard_etfs.json gerado com sucesso")
