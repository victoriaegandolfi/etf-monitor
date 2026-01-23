import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# ===============================
# CONFIG
# ===============================

ETFS = [
    "VUG", "SCHD", "IVV", "QQQ", "XLK", "IYW", "MAGS",
    "BOVA11.SA"
]

ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data" / "etfs"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "dashboard_etfs.json"

# ===============================
# FUNÇÕES
# ===============================

def get_signal(price, mm, dist_topo):
    if np.isnan(mm) or np.isnan(dist_topo):
        return "NEUTRO"

    if price < mm * 0.9 and dist_topo < -20:
        return "COMPRAR"
    elif price > mm * 1.05 and dist_topo > -5:
        return "REDUZIR"
    else:
        return "MANTER"


def cagr(prices: pd.Series):
    if len(prices) < 2:
        return np.nan
    return float((prices.iloc[-1] / prices.iloc[0]) ** (252 / len(prices)) - 1)


def max_drawdown(prices: pd.Series):
    cummax = prices.cummax()
    drawdown = prices / cummax - 1
    return float(drawdown.min())


# ===============================
# PROCESSAMENTO
# ===============================

results = []

for ticker in ETFS:
    print(f"Processando {ticker}")

    try:
        df = yf.download(ticker, period="5y", auto_adjust=True, progress=False)

        if df.empty or "Close" not in df:
            print(f"Sem dados para {ticker}")
            continue

        close = df["Close"].dropna()

        price = float(close.iloc[-1])

        mm = (
            float(close.rolling(252).mean().iloc[-1])
            if len(close) >= 252
            else np.nan
        )

        topo = (
            float(close.tail(252).max())
            if len(close) >= 252
            else np.nan
        )

        if np.isnan(mm) or np.isnan(topo):
            dist_mm = np.nan
            dist_topo = np.nan
            signal = "NEUTRO"
        else:
            dist_mm = float((price / mm - 1) * 100)
            dist_topo = float((price / topo - 1) * 100)
            signal = get_signal(price, mm, dist_topo)

        returns = close.pct_change().dropna()

        if len(returns) < 30:
            vol = np.nan
        else:
            vol = float(returns.std() * np.sqrt(252))

        result = {
            "Ticker": ticker.replace(".SA", ""),
            "Preço Atual": round(price, 2),
            "Média 200d": None if np.isnan(mm) else round(mm, 2),
            "Distância MM (%)": None if np.isnan(dist_mm) else round(dist_mm, 2),
            "Distância Topo (%)": None if np.isnan(dist_topo) else round(dist_topo, 2),
            "CAGR 5y (%)": None if np.isnan(cagr(close)) else round(cagr(close) * 100, 2),
            "Max Drawdown (%)": None if np.isnan(max_drawdown(close)) else round(max_drawdown(close) * 100, 2),
            "Volatilidade (%)": None if np.isnan(vol) else round(vol * 100, 2),
            "Sinal": signal
        }

        results.append(result)

    except Exception as e:
        print(f"Erro em {ticker}: {e}")

# ===============================
# SALVAR DASHBOARD
# ===============================

output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "data": results
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("✅ dashboard_etfs.json atualizado com sucesso")

