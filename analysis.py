import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from bcb import sgs
from config import *

ETFS = {
    "BOVA11.SA": {
        "name": "BOVA11",
        "taxa_etf": 0.0010  # 0,10% a.a.
    },
    "IVVB11.SA": {
        "name": "IVVB11",
        "taxa_etf": 0.0023  # 0,23% a.a.
    },
    "GOLD11.SA": {
        "name": "GOLD11",
        "taxa_etf": 0.0030  # 0,30% a.a.
    },
    "BIXN39.SA": {
        "name": "BIXN39",
        "taxa_etf": 0.0030  # ~0,30% a.a. (BDR ETF)
    }
}

# Custos
TAXA_B3 = 0.0003  # 0,03% a.a.

# Médias móveis
MM_CURTA = 50
MM_LONGA = 200

# Alertas
DRAWDOWN_ALERT = -0.20
DIST_MM200_ALERT = -0.05

# ----------------------------------
# PARÂMETROS DE TEMPO
# ----------------------------------
DAYS_1Y = 252
DAYS_5Y = 252 * 5

os.makedirs("data", exist_ok=True)

# ----------------------------------
# INFLAÇÃO (BACEN - SGS)
# ----------------------------------
def get_ipca_12m():
    df = sgs.get({"ipca_12m": 433})
    return df["ipca_12m"].iloc[-1] / 100


def get_ipca_5y(ipca_12m):
    return (1 + ipca_12m) ** 5 - 1


IPCA_12M = get_ipca_12m()
IPCA_5Y = get_ipca_5y(IPCA_12M)

# ----------------------------------
# DADOS DE MERCADO
# ----------------------------------
def load_data(ticker):
    df = yf.download(
        ticker,
        period="6y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )
    return df[["Close"]].dropna()


def calc_return(df, days):
    if len(df) < days:
        return np.nan
    # Ensure the result is a scalar using .item()
    return (df["Close"].iloc[-1] / df["Close"].iloc[-days] - 1).item()


# ----------------------------------
# MÉTRICAS
# ----------------------------------
def compute_metrics(df, taxa_etf):
    df["ret"] = df["Close"].pct_change()

    df["mm50"] = df["Close"].rolling(MM_CURTA).mean()
    df["mm200"] = df["Close"].rolling(MM_LONGA).mean()

    # Rentabilidade
    ret_1y_nom = calc_return(df, DAYS_1Y)
    ret_5y_nom = calc_return(df, DAYS_5Y)

    ret_1y_real = (1 + ret_1y_nom) / (1 + IPCA_12M) - 1
    ret_5y_real = (1 + ret_5y_nom) / (1 + IPCA_5Y) - 1

    ret_1y_liq = ret_1y_real - taxa_etf - TAXA_B3
    ret_5y_liq = ret_5y_real - (taxa_etf + TAXA_B3) * 5

    # Risco
    vol_1y = df["ret"].tail(DAYS_1Y).std() * np.sqrt(252)

    cum = (1 + df["ret"]).cumprod()
    peak = cum.cummax()
    drawdown = cum / peak - 1

    return {
        "price": round(df["Close"].iloc[-1].item(), 2),
        "returns": {
            "1y": {
                "nominal": round(ret_1y_nom, 4),
                "real": round(ret_1y_real, 4),
                "liquido": round(ret_1y_liq, 4)
            },
            "5y": {
                "nominal": round(ret_5y_nom, 4),
                "real": round(ret_5y_real, 4),
                "liquido": round(ret_5y_liq, 4)
            }
        },
        "risk": {
            "vol_1y": round(vol_1y, 4),
            "drawdown_max": round(drawdown.min(), 4),
            "drawdown_atual": round(drawdown.iloc[-1], 4),
            "dist_mm200": round(
                (df["Close"].iloc[-1] / df["mm200"].iloc[-1] - 1).item(),
                4
            )
        }
    }


def generate_alerts(metrics):
    alerts = []

    if metrics["risk"]["dist_mm200"] < DIST_MM200_ALERT:
        alerts.append("Preço abaixo da MM200")

    if metrics["risk"]["drawdown_atual"] < DRAWDOWN_ALERT:
        alerts.append("Drawdown elevado")

    if metrics["returns"]["1y"]["real"] < 0:
        alerts.append("Retorno real negativo (1a)")

    return alerts


# ----------------------------------
# PIPELINE FINAL — 4 ETFs
# ----------------------------------
summary = {
    "ipca": {
        "ipca_12m": round(IPCA_12M, 4),
        "ipca_5y_proxy": round(IPCA_5Y, 4)
    },
    "etfs": {}
}

for ticker, cfg in ETFS.items():
    print(f"Processando {cfg['name']} ({ticker})")

    df = load_data(ticker)
    metrics = compute_metrics(df, cfg["taxa_etf"])
    alerts = generate_alerts(metrics)

    result = {
        "ticker": ticker,
        "name": cfg["name"],
        **metrics,
        "alerts": alerts
    }

    with open(f"data/{cfg['name']}.json", "w") as f:
        json.dump(result, f, indent=2)

    summary["etfs"][cfg["name"]] = result

with open("data/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
