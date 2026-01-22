import streamlit as st
import pandas as pd
import json
from pathlib import Path
import numpy as np

# ===============================
# CONFIG
# ===============================

st.set_page_config(
    page_title="Dashboard de Ações",
    layout="wide"
)

DATA_FILE = Path("data/stocks/dashboard_stocks.json")

# ===============================
# LOAD DATA
# ===============================

with open(DATA_FILE, "r") as f:
    raw = json.load(f)

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
# FILTERS
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

# ===============================
# CALENDÁRIO DE DIVIDENDOS
# ===============================

st.subheader("💰 Calendário de Dividendos (meses recorrentes)")

months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
          "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

calendar_rows = []

for _, r in df.iterrows():
    row = {"Ticker": r["Ticker"]}
    for i, m in enumerate(months, start=1):
        row[m] = "✔️" if i in r["Dividendos Meses"] else ""
    calendar_rows.append(row)

calendar_df = pd.DataFrame(calendar_rows)

st.dataframe(calendar_df, use_container_width=True)

# ===============================
# EXPOSIÇÃO DA CARTEIRA
# ===============================

st.subheader("📦 Exposição da Carteira")

exposure_cols = [
    "Ticker",
    "Quantidade",
    "Preço Médio",
    "Valor Investido",
    "Valor Atual",
    "Sinal"
]

exposure_df = df[df["Quantidade"].notna()][exposure_cols].copy()

if not exposure_df.empty:
    total_value = exposure_df["Valor Atual"].sum()

    exposure_df["% Carteira"] = (
        exposure_df["Valor Atual"] / total_value * 100
    ).round(2)

    st.dataframe(
        exposure_df.sort_values("% Carteira", ascending=False),
        use_container_width=True
    )
else:
    st.info("Nenhuma posição informada em exposure.csv")

# ===============================
# FOOTER
# ===============================

st.caption("Modelo fundamentalista com Número de Graham • Projeto pessoal de investimentos")



