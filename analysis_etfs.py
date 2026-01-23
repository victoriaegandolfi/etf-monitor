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

    # EUA
    "VUG": "VUG",
    "SCHD": "SCHD",
    "IVV": "IVV",
    "QQQ": "QQQ",
    "XLK": "XLK",
    "IYW": "IYW",
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
    # Média móvel 1 ano
    # ---------------------
    if len(close) >= 252:
        mm = float(close.rolling(252).mean().iloc[-1])
        topo = float(close.tail(252).max())
    else:
        mm = np.nan
        topo = np.nan

    # ---------------------
    # Retornos
    # ---------------------
    ret_1a = (
        price / float(close.iloc[-252]) - 1
        if len(close) >= 252 else np.nan
    )

    ret_5a = (
        annualized_return(close.tail(252 * 5))
        if len(close) >= 252 * 5 else np.nan
    )

    ret_real_1a = (
        (1 + ret_1a) / (1 + IPCA_12M) - 1
        if not np.isnan(ret_1a) else np.nan
    )

    # ---------------------
    # Risco
    # ---------------------
    vol = close.pct_change().std() * np.sqrt(252)
    dd = max_drawdown(close)

    # ---------------------
    # Sinal
    # ---------------------
    if np.isnan(mm) or np.isnan(topo):
        dist_mm = np.nan
        dist_topo = np.nan
        signal = "NEUTRO"
    else:
        dist_mm = (price / mm - 1) * 100
        dist_topo = (price / topo - 1) * 100
        signal = get_signal(price, mm, dist_topo)

    # ---------------------
    # Histórico normalizado
    # ---------------------
    hist = (close / close.iloc[0] * 100).reset_index()
    hist.columns = ["date", "price_norm"]
    hist["date"] = hist["date"].astype(str)

    hist.to_json(
        DATA_DIR / f"{etf}_history.json",
        orient="records"
    )

    # ---------------------
    # Outputs
    # ---------------------
    summary.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Retorno 1a (%)": None if np.isnan(ret_1a) else round(ret_1a * 100, 2),
        "Retorno real 1a (%)": None if np.isnan(ret_real_1a) else round(ret_real_1a * 100, 2),
        "Retorno 5a a.a. (%)": None if np.isnan(ret_5a) else round(ret_5a * 100, 2),
        "Volatilidade (%)": None if np.isnan(vol) else round(vol * 100, 2),
        "Drawdown máx (%)": None if np.isnan(dd) else round(dd * 100, 2)
    })

    signals.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Dist. MM 1a (%)": None if np.isnan(dist_mm) else round(dist_mm, 2),
        "Dist. topo 1a (%)": None if np.isnan(dist_topo) else round(dist_topo, 2),
        "Sinal": signal
    })

# =====================================================
# SALVA DASHBOARD
# =====================================================

output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "ipca_12m": round(IPCA_12M * 100, 2),
    "summary": summary,
    "signals": signals
}

with open(DATA_DIR / "dashboard_etfs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("✅ analysis_etfs.py finalizado com sucesso")


    # ---------------------
