import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from bcb import sgs

# =====================================================
# CONFIGURAÇÕES
# =====================================================

ETFS = {
    # Brasil
    "BOVA11": "BOVA11.SA",
    "IVVB11": "IVVB11.SA",
    "GOLD11": "GOLD11.SA",
    "BIXN39": "BIXN39.SA",

    # EUA
    "IVV": "IVV",
    "VUG": "VUG",
    "SCHD": "SCHD",
    "QQQ": "QQQ",
    "XLK": "XLK",
    "IYW": "IYW",

    # Big Tech / MAGs proxy
    "MAGS": "MAGS"
}


ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data" / "etfs"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def scalar(x):
    if isinstance(x, pd.Series):
        if x.empty:
            return np.nan
        return float(x.iloc[-1])
    try:
        return float(x)
    except Exception:
        return np.nan


def get_ipca_12m():
    df = sgs.get({"ipca": 433})
    return scalar(df["ipca"]) / 100


def annualized_return(prices: pd.Series):
    prices = prices.dropna()
    if len(prices) < 2:
        return np.nan
    return float((prices.iloc[-1] / prices.iloc[0]) ** (252 / len(prices)) - 1)


def max_drawdown(prices: pd.Series):
    prices = prices.dropna()
    if prices.empty:
        return np.nan
    cummax = prices.cummax()
    return float((prices / cummax - 1).min())


def get_signal(price, mm, dist_topo):
    if price < mm * 0.90 and dist_topo < -20:
        return "COMPRAR"
    elif price > mm * 1.20 or dist_topo > -5:
        return "REDUZIR"
    else:
        return "NEUTRO"


# =====================================================
# IPCA
# =====================================================

IPCA_12M = get_ipca_12m()

# =====================================================
# PROCESSAMENTO PRINCIPAL
# =====================================================

summary = []
signals = []

for etf, ticker in ETFS.items():
    print(f"Processando {etf}")

    df = yf.download(
        ticker,
        period="6y",
        auto_adjust=True,
        progress=False
    )

    if df.empty or "Close" not in df.columns:
        continue

    close = df["Close"].dropna()
    if len(close) < 60:
        continue

    # ---------------------
    # Preço atual
    # ---------------------
    price = float(close.iloc[-1])

    # ---------------------
