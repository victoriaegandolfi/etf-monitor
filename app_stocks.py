# ===============================
# EXPOSIÇÃO DA CARTEIRA
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
