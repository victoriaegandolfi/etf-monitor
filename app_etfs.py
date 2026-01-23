import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from pathlib import Path

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
    st.error("dashboard_etfs.json não encontrado em data/etfs")
    st.stop()

with open(DASH_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

if "data" not in raw or len(raw["data"]) == 0:
    st.warning("Dashboard carregado, mas sem dados de ETFs.")
    st.stop()

df = pd.DataFrame(raw["data"])

if "Ticker" not in df.columns:
    st.error("Coluna 'Ticker' não encontrada no dashboard_etfs.json")
    st.stop()

# ===============================
# HEADER
# ===============================

st.title("📊 Monitor de ETFs")
st.caption(f"Atualizado em: {raw.get('updated_at', '—')}")

# ===============================
# SIDEBAR
# ===============================

st.sidebar.header("🔎 Filtros")

if "Sinal" in df.columns:
    signal_filter = st.sidebar.multiselect(
        "Sinal",
        options=sorted(df["Sinal"].dropna().unique()),
        default=list(df["Sinal"].dropna().unique())
    )
else:
    signal_filter = []

selected_etfs = st.sidebar.multiselect(
    "ETFs (gráfico)",
    options=sorted(df["Ticker"].unique()),
    default=sorted(df["Ticker"].unique())
)

# ===============================
# FILTERS
# ===============================

filtered = df.copy()

if signal_filter and "Sinal" in filtered.columns:
    filtered = filtered[filtered["Sinal"].isin(signal_filter)]

# ===============================
# TABELA PRINCIPAL
# ===============================

st.subheader("📌 Visão Geral")

display_cols = [
    "Ticker",
    "Preço Atual",
    "MM 1 ano",
    "Topo 1 ano",
    "Dist MM (%)",
    "Dist Topo (%)",
    "Sinal"
]

existing_cols = [c for c in display_cols if c in filtered.columns]

table_df = filtered[existing_cols].copy()

# ordenação segura
if "Dist MM (%)" in table_df.columns:
    table_df = table_df.sort_values("Dist MM (%)", ascending=True)
elif "Dist Topo (%)" in table_df.columns:
    table_df = table_df.sort_values("Dist Topo (%)", ascending=True)
else:
    table_df = table_df.sort_values("Ticker")

st.dataframe(
    table_df.reset_index(drop=True),
    use_container_width=True
)

# ===============================
# GRÁFICO DE PREÇO (BASE 100)
# ===============================

st.subheader("📈 Preço ao longo do tempo (Base 100)")

if not selected_etfs:
    st.info("Selecione ao menos um ETF para o gráfico.")
else:
    fig, ax = plt.subplots(figsize=(11, 5))
    plotted = False

    for ticker in selected_etfs:
        hist_file = DATA_DIR / f"{ticker}_history.json"

        if not hist_file.exists():
            continue

        hist = pd.read_json(hist_file)

        if {"date", "price_norm"}.issubset(hist.columns):
            ax.plot(
                pd.to_datetime(hist["date"]),
                hist["price_norm"],
                label=ticker
            )
            plotted = True

    if plotted:
        ax.set_ylabel("Índice (Base 100)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.warning("Nenhum histórico encontrado para os ETFs selecionados.")

# ===============================
# AJUDA
# ===============================

with st.expander("ℹ️ Como interpretar os sinais"):
    st.markdown("""
**🟢 COMPRAR**  
Preço bem abaixo da média móvel de 1 ano e distante do topo recente.

**🟡 NEUTRO**  
Sem desvios relevantes em relação ao histórico.

**🔴 REDUZIR**  
Preço muito acima da média ou próximo do topo do último ano.
""")
