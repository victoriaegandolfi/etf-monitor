import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from bcb import sgs

# =====================================================
# Configurações
# =====================================================
ETFS = {
    "BOVA11": "BOVA11.SA",
    "IVVB11": "IVVB11.SA",
    "GOLD11": "GOLD11.SA",
    "BIXN39": "BIXN39.SA"
}



DATA_DIR = Path("data/etfs")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# Funções utilitárias (ESCALARES APENAS)
# =====================================================
def scalar(x):
    """Converte qualquer input para float escalar ou np.nan"""
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

def max_last_year(close: pd.Series):
    if close.empty:
        return np.nan

    last_date = close.index[-1]
    start_date = last_date - pd.DateOffset(years=1)

    window = close[close.index >= start_date]

    if window.empty:
        return np.nan

    return float(window.max())



# =====================================================
# IPCA
# =====================================================
IPCA_12M = get_ipca_12m()

# =====================================================
# Processamento principal
# =====================================================
summary = []
signals = []

for etf, ticker in ETFS.items():
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
    # Preço
    # ---------------------
    price = scalar(close.iloc[-1])

    # ---------------------
    # Média móvel 1 ano
    # ---------------------
    ma_1y = scalar(close.rolling(252).mean().iloc[-1])

    # ---------------------
    # Retornos
    # ---------------------
    ret_1a = (
        scalar(price / scalar(close.iloc[-252]) - 1)
        if len(close) >= 252 else np.nan
    )

    ret_5a = (
        scalar(annualized_return(close.tail(252 * 5)))
        if len(close) >= 252 * 5 else np.nan
    )

    ret_real_1a = (
        scalar((1 + ret_1a) / (1 + IPCA_12M) - 1)
        if not pd.isna(ret_1a) else np.nan
    )

    # ---------------------
    # Risco
    # ---------------------
    vol = scalar(close.pct_change().std()) * np.sqrt(252)
    dd = scalar(max_drawdown(close))

    # ---------------------
    # Topo 1 ano
    # ---------------------
    max_1a = max_last_year(close)

    # ---------------------
    # Sinal de preço
    # ---------------------
    dist_ma = np.nan
    dist_topo = np.nan
    signal = "NEUTRO"

    if not pd.isna(ma_1y) and not pd.isna(max_1a):
        dist_ma = scalar(price / ma_1y - 1)
        dist_topo = scalar(price / max_1a - 1)

        if dist_ma < -0.10 and dist_topo < -0.20:
            signal = "COMPRAR"
        elif dist_ma > 0.20 or dist_topo > -0.05:
            signal = "REDUZIR"

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
        "Retorno 1a (%)": None if pd.isna(ret_1a) else round(ret_1a * 100, 2),
        "Retorno real 1a (%)": None if pd.isna(ret_real_1a) else round(ret_real_1a * 100, 2),
        "Retorno 5a a.a. (%)": None if pd.isna(ret_5a) else round(ret_5a * 100, 2),
        "Volatilidade (%)": None if pd.isna(vol) else round(vol * 100, 2),
        "Drawdown máx (%)": None if pd.isna(dd) else round(dd * 100, 2)
    })

    signals.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Dist. MM 1a (%)": None if pd.isna(dist_ma) else round(dist_ma * 100, 2),
        "Dist. topo 1a (%)": None if pd.isna(dist_topo) else round(dist_topo * 100, 2),
        "Sinal": signal
    })

# =====================================================
# Salva JSON principal
# =====================================================
output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "ipca_12m": round(IPCA_12M * 100, 2),
    "summary": summary,
    "signals": signals
}
from pathlib import Path

# Diretório raiz do repo
ROOT_DIR = Path(__file__).parent.resolve()

# Pasta de dados específica
DATA_DIR = ROOT_DIR / "data" / "etfs"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Salvar JSON
with open(DATA_DIR / "dashboard_etfs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

