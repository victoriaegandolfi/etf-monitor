import json
import streamlit as st
import pandas as pd

import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Monitor de ETFs", layout="wide")

DATA_DIR = Path("data")

with open(DATA_DIR / "dashboard.json") as f:
    data = json.load(f)

df_summary = pd.DataFrame(data["summary"])
df_signals = pd.DataFrame(data["signals"])

# =====================
# Header
# =====================
st.title("📊 Monitor de ETFs")
st.caption(
    f"Última atualização: {data['updated_at']} | "
    f"IPCA 12m: {data['ipca_12m']}%"
)

# =====================
# Tabela 1 — Resumo
# =====================
st.subheader("Resumo dos ETFs")
st.dataframe(df_summary, use_container_width=True)

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

st.dataframe(
    df_signals.style.applymap(color_signal, subset=["Sinal"]),
    use_container_width=True
)

# =====================
# Gráfico comparativo
# =====================
st.subheader("Comparação de preço (base 100)")

selected = st.multiselect(
    "Selecione os ETFs",
    options=df_summary["ETF"].tolist(),
    default=df_summary["ETF"].tolist()
)

fig, ax = plt.subplots(figsize=(10, 5))

for etf in selected:
    hist = pd.read_json(DATA_DIR / f"{etf}_history.json")
    ax.plot(hist["date"], hist["price_norm"], label=etf)

ax.set_ylabel("Índice (base 100)")
ax.legend()
ax.grid(True)

st.pyplot(fig)

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
