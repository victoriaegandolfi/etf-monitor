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

# ===============================
# CALENDÁRIO DE DIVIDENDOS
# ===============================
st.subheader("💰 Calendário de Dividendos (meses recorrentes)")

months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
          "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

calendar_rows = []

for _, r in df.iterrows():
    row_calendar = {"Ticker": r["Ticker"]}
    for i, m in enumerate(months, start=1):
        row_calendar[m] = "✔️" if i in r.get("Dividendos Meses", []) else ""
    calendar_rows.append(row_calendar)

calendar_df = pd.DataFrame(calendar_rows)
st.dataframe(calendar_df, use_container_width=True)

# ===============================
# EXPOSIÇÃO DA CARTEIRA (MULTI-OWNER)
# ===============================
st.subheader("📦 Exposição da Carteira")

exposure_rows = []

for _, r in df.iterrows():
    ticker = r["Ticker"]
    signal = r["Sinal"]
    exp_list = r.get("Exposicao", [])
    
    for exp in exp_list:
        exposure_rows.append({
            "Ticker": ticker,
            "Owner": exp.get("owner", "Desconhecido"),
            "Quantidade": exp.get("quantidade", np.nan),
            "Preço Médio": exp.get("preco_medio", np.nan),
            "Valor Investido": exp.get("valor_investido", np.nan),
            "Valor Atual": exp.get("valor_atual", np.nan),
            "Sinal": signal
        })

if exposure_rows:
    exposure_df = pd.DataFrame(exposure_rows)

    # % da carteira por owner
    exposure_df["% Carteira"] = exposure_df.groupby("Owner")["Valor Atual"].apply(
        lambda x: (x / x.sum() * 100).round(2)
    )

    st.dataframe(
        exposure_df.sort_values(["Owner", "% Carteira"], ascending=[True, False]),
        use_container_width=True
    )
else:
    st.info("Nenhuma posição informada em exposure.csv")

# ===============================
# FOOTER
# ===============================
st.caption("Modelo fundamentalista com Número de Graham • Projeto pessoal de investimentos")

