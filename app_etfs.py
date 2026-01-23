import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt

# ===============================
# CONFIG
# ===============================

st.set_page_config(page_title="📊 Monitor de ETFs", layout="wide")

ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data" / "etfs"
DASH_FILE = DATA_DIR / "dashboard_etfs.json"

# ===============================
# LOAD DATA
# ===============================

if not DASH_FILE.exists():
    st.error("Arquivo dashboard_etfs.json não encontrado.")
    st.stop()

with open(DASH_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

if "data" not in raw or len(raw["data"]) == 0:
    st.warning("Dashboard carregado, mas sem dados de ETFs.")
    st.stop()

df = pd.DataFrame(raw["data"])

# ===============================
# HEADER
# ===============================

st.title("📊 Monitor de ETFs")
st.caption(f"Última atualização: {raw['updated_at']}")

# ===============================
# TABELA PRINCIPAL
# ===============================

st.subheader("📌 Visão Geral")

display_cols = [
    "Ticker",
    "Preço Atual",
    "Média 200d",
    "Distância MM (%)",
    "Distância Topo (%)",
    "CAGR 5y (%)",
    "Volatilidade (%)",
    "Sinal"
]

st.dataframe(
    df[display_cols]
    .sort_values("Distância MM (%)", ascending=True)
    .reset_index(drop=True),
    use_container_width=True
)

# ===============================
# FILTROS
# ===============================

st.subheader("🎯 Análise individual")

selected = st.selectbox(
    "Selecione o ETF",
    sorted(df["Ticker"].unique())
)

row = df[df["Ticker"] == selected].iloc[0]

# ===============================
# MÉTRICAS
# ===============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Preço Atual", f"${row['Preço Atual']}")
col2.metric("Média 200d", "-" if pd.isna(row["Média 200d"]) else f"${row['Média 200d']}")
col3.metric("Distância MM", "-" if pd.isna(row["Distância MM (%)"]) else f"{row['Distância MM (%)']}%")
col4.metric("Sinal", row["Sinal"])

# ===============================
# AJUDA
# ===============================

with st.expander("ℹ️ Como interpretar os sinais"):
    st.markdown("""
**🟢 COMPRAR**  
Preço bem abaixo da média de 1 ano e distante do topo recente.

**🟡 MANTER**  
Preço próximo da média ou sem distorções relevantes.

**🔴 REDUZIR**  
Preço muito acima da média ou próximo do topo.
""")

# ===============================
# FOOTER
# ===============================

st.caption("Modelo quantitativo • ETFs globais e Brasil • Projeto pessoal de investimentos")
