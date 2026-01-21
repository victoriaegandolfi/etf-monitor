import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# ===============================
# CONFIGURAÇÕES
# ===============================

FUNDAMENTAL_BR = ["ITUB4.SA", "BBAS3.SA", "WEGE3.SA", "ABEV3.SA", "VALE3.SA"]
FUNDAMENTAL_US = ["EUAQ11.SA", "AAPL", "MSFT", "JNJ", "BRK-B"]

DIVIDEND_BR = ["TAEE11.SA", "TRPL4.SA", "ITSA4.SA", "PETR4.SA", "BBAS3.SA"]
DIVIDEND_US = ["EUAQ11.SA", "KO", "PG", "JNJ", "VZ"]

ALL_TICKERS = sorted(set(
    FUNDAMENTAL_BR + FUNDAMENTAL_US + DIVIDEND_BR + DIVIDEND_US
))

DATA_DIR = Path("data/stocks")
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPOSURE_FILE = DATA_DIR / "exposure.csv"

# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def get_last_price(ticker):
    hist = ticker.history(period="5y", auto_adjust=True)
    if hist.empty:
        return np.nan
    return float(hist["Close"].iloc[-1])


def calc_graham_number(info):
    eps = info.get("trailingEps")
    bvps = info.get("bookValue")

    if eps is None or bvps is None:
        return np.nan
    if eps <= 0 or bvps <= 0:
        return np.nan

    return float(np.sqrt(22.5 * eps * bvps))


def calc_signal(price, graham):
    if np.isnan(price) or np.isnan(graham):
        return "Sem dados"

    diff = (price - graham) / graham

    if diff <= -0.15:
        return "Comprar"
    elif diff >= 0.10:
        return "Reduzir"
    else:
        return "Manter"


def dividend_calendar(ticker):
    divs = ticker.dividends
    if divs.empty:
        return []

    last_years = divs[divs.index >= (divs.index.max() - pd.DateOffset(years=5))]
    months = sorted(set(last_years.index.month))

    return months


# ===============================
# LEITURA DA EXPOSIÇÃO (MANUAL)
# ===============================

if EXPOSURE_FILE.exists():
    exposure_df = pd.read_csv(EXPOSURE_FILE)
else:
    exposure_df = pd.DataFrame(columns=["ticker", "quantidade", "preco_medio"])


# ===============================
# LOOP PRINCIPAL
# ===============================

results = []

for symbol in ALL_TICKERS:
    print(f"Processando {symbol}")

    ticker = yf.Ticker(symbol)
    info = ticker.info

    price = get_last_price(ticker)
    graham = calc_graham_number(info)
    signal = calc_signal(price, graham)

    diff_pct = (
        (price - graham) / graham if not np.isnan(price) and not np.isnan(graham) else np.nan
    )

    # Dividendos
    div_months = dividend_calendar(ticker)

    # Estratégias
    strategies = []
    if symbol in FUNDAMENTAL_BR + FUNDAMENTAL_US:
        strategies.append("Fundamentalista")
    if symbol in DIVIDEND_BR + DIVIDEND_US:
        strategies.append("Dividendos")

    # Exposição
    exp = exposure_df[exposure_df["ticker"] == symbol]

    owners = []
    positions = []
    
    for _, row in exp.iterrows():
        qty = float(row["quantidade"])
        avg_price = float(row["preco_medio"])
        invested = qty * avg_price
        current_value = qty * price if not np.isnan(price) else np.nan
    
        positions.append({
            "owner": row["owner"],
            "quantidade": qty,
            "preco_medio": avg_price,
            "valor_investido": round(invested, 2),
            "valor_atual": round(current_value, 2) if not np.isnan(current_value) else None
        })
    if not exp.empty:
        qty = float(exp["quantidade"].iloc[0])
        avg_price = float(exp["preco_medio"].iloc[0])
        invested = qty * avg_price
        current_value = qty * price if not np.isnan(price) else np.nan
    else:
        qty = avg_price = invested = current_value = np.nan

    results.append({
        "Ticker": symbol,
        "Preço Atual": round(price, 2) if not np.isnan(price) else None,
        "Preço Justo (Graham)": round(graham, 2) if not np.isnan(graham) else None,
        "Desvio (%)": round(diff_pct * 100, 2) if not np.isnan(diff_pct) else None,
        "Sinal": signal,
        "Estratégias": strategies,
        "Dividendos Meses": div_months,
        "Quantidade": qty,
        "Preço Médio": avg_price,
        "Valor Investido": round(invested, 2) if not np.isnan(invested) else None,
        "Valor Atual": round(current_value, 2) if not np.isnan(current_value) else None,
        "Exposicao": positions

    })


# ===============================
# SALVAR JSON FINAL
# ===============================

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "data": results
}

with open(DATA_DIR / "dashboard_stocks.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)


print("✅ analysis_stocks.py finalizado com sucesso")
