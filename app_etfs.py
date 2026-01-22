import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Monitor de ETFs", layout="wide")

# ---------------------
# Diretório dos dados
# ---------------------
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data" / "etfs"
dashboard_file = DATA_DIR / "dashboard_etfs.json"

# ---------------------
# Carrega JSON
# ---------------------
try:
    with open(dashboard_file, "r", encoding="utf-8") as f:
        raw = json.load(f)
except FileNotFoundError:
    st.error("❌ Arquivo de dados dos ETFs não encontrado!")
    st.stop()

# ---------------------
# DataFrames
# ---------------------
df_summary = pd.DataFrame(raw.get("summary", []))
df_signals = pd.DataFrame(raw.get("signals", []))

# =====================
# Header
# =====================
st.title("📊 Monitor de ETFs")
st.caption(
    f"Última atualização: {raw.get('updated_at', 'N/A')} | "
    f"IPCA 12m: {raw.get('ipca_12m', 'N/A')}%"
)

# =====================
# Tabela 1 — Resumo
# =====================
st.subheader("Resumo dos ETFs")
if not df_summary.empty:
    st.dataframe(df_summary, use_container_width=True)
else:
    st.info("Nenhum dado de resumo disponível.")

# =====================
# Tabela 2 — Sinais
# =====================
st.subheader("Sinais de preço (MM 1 ano)")

def color_signal(val):
    if val == "COMPRAR":
        return "background-color: #c6f6d5"
    if val == "REDUZIR":
        return "background-color: #fed7d7"
    return ""

if not df_signals.empty:
    st.dataframe(
        df_signals.style.applymap(color_signal, subset=["Sinal"]),
        use_container_width=True
    )
else:
    st.info("Nenhum sinal disponível.")

# =====================
# Gráfico comparativo
# =====================
st.subheader("Comparação de preço (base 100)")

selected = st.multiselect(
    "Selecione os ETFs",
    options=df_summary["ETF"].tolist() if not df_summary.empty else [],
    default=df_summary["ETF"].tolist() if not df_summary.empty else []
)

if selected:
    fig, ax = plt.subplots(figsize=(10, 5))

    for etf in selected:
        hist_file = DATA_DIR / f"{etf}_history.json"
        if hist_file.exists():
            hist = pd.read_json(hist_file)
            ax.plot(hist["date"], hist["price_norm"], label=etf)
        else:
            st.warning(f"Histórico de {etf} não encontrado.")

    ax.set_ylabel("Índice (base 100)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
else:
    st.info("Selecione pelo menos um ETF para ver o gráfico.")

# =====================
# Ajuda
# =====================
with st.expander("ℹ️ Como interpretar os sinais"):
    st.markdown("""
**🟢 COMPRAR**  
Preço bem abaixo da média móvel de 1 ano e distante do topo recente.

**🔴 REDUZIR**  
Preço muito acima da média ou próximo do topo do último ano.

**🟡 NEUTRO**  
Sem desvios relevantes.
""")
