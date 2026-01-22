import streamlit as st
import pandas as pd
import json
from pathlib import Path
import numpy as np

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(page_title="Monitor de Stocks", layout="wide")

# Caminho absoluto baseado no arquivo atual
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data" / "stocks"
dashboard_file = DATA_DIR / "dashboard_stocks.json"

# ===============================
# CARREGAR DADOS
# ===============================
with open(dashboard_file, "r", encoding="utf-8") as f:
    raw = json.load(f)

# Transformar a lista de resultados em DataFrame
df = pd.DataFrame(raw["data"])

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("📊 Filtros")

strategy = st.sidebar.selectbox(
    "Estratégia",
    ["Todas", "Fundamentalista", "Dividendos"]
)

signal_filter = st.sidebar.multiselect(
    "Sinal",
    ["Comprar", "Manter", "Reduzir"],
    default=["Comprar", "Manter", "Reduzir"]
)

selected_ticker = st.sidebar.selectbox(
    "Ativo (para gráfico)",
    sorted(df["Ticker"].unique())
)

# ===============================
# FILTROS
# ===============================
filtered = df.copy()

if strategy != "Todas":
    filtered = filtered[filtered["Estratégias"].apply(lambda x: strategy in x)]

filtered = filtered[filtered["Sinal"].isin(signal_filter)]

# ===============================
# HEADER
# ===============================
st.title("📈 Dashboard de Ações")
st.caption(f"Atualizado em: {raw['updated_at']}")

# ===============================
# TABELA PRINCIPAL (DECISÃO)
# ===============================
st.subheader("📌 Visão Geral — Decisão")

display_cols = [
    "Ticker",
    "Preço Atual",
    "Preço Justo (Graham)",
    "Desvio (%)",
    "Sinal"
]

st.dataframe(
    filtered[display_cols]
    .sort_values("Desvio (%)", ascending=True)
    .reset_index(drop=True),
    use_container_width=True
)

# ===============================
# GRÁFICO PREÇO x GRAHAM
# ===============================
st.subheader(f"📉 Preço x Graham — {selected_ticker}")

row = df[df["Ticker"] == selected_ticker].iloc[0]

chart_df = pd.DataFrame({
    "Valor": ["Preço Atual", "Preço Justo (Graham)"],
    "Preço": [row["Preço Atual"], row["Preço Justo (Graham)"]]
})

st.bar_chart(chart_df.set_index("Valor"))
st.caption(f"Sinal atual: **{row['Sinal']}**")

# =======================


