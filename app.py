import json
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Monitor de ETFs",
    layout="wide"
)

# ----------------------------------
# LOAD DATA
# ----------------------------------
@st.cache_data
def load_data():
    with open("data/summary.json") as f:
        return json.load(f)

data = load_data()
etfs = data["etfs"]
ipca = data["ipca"]

# ----------------------------------
# HEADER
# ----------------------------------
st.title("📊 Monitor de ETFs")
st.caption(
    f"IPCA 12m: {ipca['ipca_12m']*100:.2f}% | "
    f"Proxy IPCA 5a: {ipca['ipca_5y_proxy']*100:.2f}%"
)

# ----------------------------------
# KPI CARDS
# ----------------------------------
st.subheader("📌 Visão Geral (1 ano)")

cols = st.columns(len(etfs))

for col, (name, d) in zip(cols, etfs.items()):
    with col:
        st.metric(
            label=name,
            value=f"R$ {d['price']}",
            delta=f"{d['returns']['1y']['real']*100:.2f}% real"
        )

        if d["alerts"]:
            for a in d["alerts"]:
                st.warning(a)

# ----------------------------------
# TABELA COMPARATIVA
# ----------------------------------
st.divider()
st.subheader("📈 Comparação de Desempenho")

rows = []

for name, d in etfs.items():
    rows.append({
        "ETF": name,
        "Preço": d["price"],
        "Ret 1a Nom (%)": d["returns"]["1y"]["nominal"] * 100,
        "Ret 1a Real (%)": d["returns"]["1y"]["real"] * 100,
        "Ret 5a Real (%)": d["returns"]["5y"]["real"] * 100,
        "Vol 1a (%)": d["risk"]["vol_1y"] * 100,
        "DD Máx (%)": d["risk"]["drawdown_max"] * 100,
        "Dist MM200 (%)": d["risk"]["dist_mm200"] * 100,
    })

df = pd.DataFrame(rows).set_index("ETF")

st.dataframe(
    df.style
    .format("{:.2f}")
    .background_gradient(cmap="RdYlGn", subset=["Ret 1a Real (%)", "Ret 5a Real (%)"])
    .background_gradient(cmap="RdYlGn_r", subset=["Vol 1a (%)", "DD Máx (%)"])
)

# ----------------------------------
# RANKINGS
# ----------------------------------
st.divider()
st.subheader("🏆 Rankings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Melhor retorno real (1 ano)**")
    st.table(
        df[["Ret 1a Real (%)"]]
        .sort_values("Ret 1a Real (%)", ascending=False)
        .head(4)
    )

with col2:
    st.markdown("**Menor risco (volatilidade 1 ano)**")
    st.table(
        df[["Vol 1a (%)"]]
        .sort_values("Vol 1a (%)")
        .head(4)
    )

# ----------------------------------
# ALERTAS CONSOLIDADOS
# ----------------------------------
st.divider()
st.subheader("🚨 Alertas Ativos")

alerts = []

for name, d in etfs.items():
    for a in d["alerts"]:
        alerts.append(f"**{name}** → {a}")

if alerts:
    for a in alerts:
        st.error(a)
else:
    st.success("Nenhum alerta crítico no momento ✅")

# ----------------------------------
# FOOTER
# ----------------------------------
st.caption("Dados: Yahoo Finance | IPCA: Banco Central (SGS)")
