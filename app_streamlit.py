import streamlit as st


st.set_page_config(
    page_title="Simulatore Forfettario 2025+",
    page_icon="📊",
    layout="wide",
)


SETTORI = {
    "Attività professionali, scientifiche, tecniche": 78,
    "Costruzioni e attività immobiliari": 86,
    "Intermediari commercio": 62,
    "Commercio all'ingrosso e dettaglio": 40,
    "Servizi alloggio e ristorazione": 40,
    "Altre attività economiche": 67,
}


def calcola_forfettario(
    ricavi,
    coefficiente,
    contributi_anno_prec,
    aliquota_imposta,
    tipo_cassa,
    riduzione_contrib=0,
):
    reddito_imponibile_lordo = ricavi * (coefficiente / 100)
    reddito_imponibile_netto = max(0, reddito_imponibile_lordo - contributi_anno_prec)

    imposta_sostitutiva = reddito_imponibile_netto * (aliquota_imposta / 100)

    if tipo_cassa == "Gestione Separata INPS":
        aliquota_inps = 26.07
        contributi_inps = reddito_imponibile_lordo * (aliquota_inps / 100)
        riduzione_applicata = 0
    else:
        contributo_fisso = 4460.64
        minimale = 18555
        eccedenza = max(0, reddito_imponibile_lordo - minimale)
        aliquota_eccedenza = 24

        if riduzione_contrib == 35:
            contributo_fisso *= 0.65
            aliquota_eccedenza *= 0.65
            riduzione_applicata = 35
        elif riduzione_contrib == 50:
            contributo_fisso *= 0.50
            aliquota_eccedenza *= 0.50
            riduzione_applicata = 50
        else:
            riduzione_applicata = 0

        contributi_variabili = eccedenza * (aliquota_eccedenza / 100)
        contributi_inps = contributo_fisso + contributi_variabili

    totale_imposte_contributi = imposta_sostitutiva + contributi_inps
    tax_rate = (totale_imposte_contributi / ricavi) * 100 if ricavi else 0
    netto = ricavi - totale_imposte_contributi

    return {
        "reddito_lordo": reddito_imponibile_lordo,
        "reddito_netto": reddito_imponibile_netto,
        "imposta": imposta_sostitutiva,
        "contributi": contributi_inps,
        "totale": totale_imposte_contributi,
        "tax_rate": tax_rate,
        "netto": netto,
        "riduzione": riduzione_applicata,
    }


def euro(val):
    return f"€ {val:,.2f}"


st.title("📊 Simulatore Regime Forfettario 2025+")
st.caption("Versione avanzata: confronto scenari, breakdown visivo e analisi del netto")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Preset rapidi")
    preset = st.selectbox(
        "Carica un profilo",
        [
            "Personalizzato",
            "Freelance consulente (78%)",
            "Commercio al dettaglio (40%)",
            "Artigiano con riduzione 35%",
        ],
    )

preset_values = {
    "Personalizzato": (50000, "Attività professionali, scientifiche, tecniche", 5000, 15, "Gestione Separata INPS", 0),
    "Freelance consulente (78%)": (45000, "Attività professionali, scientifiche, tecniche", 4500, 5, "Gestione Separata INPS", 0),
    "Commercio al dettaglio (40%)": (70000, "Commercio all'ingrosso e dettaglio", 6500, 15, "Artigiani e Commercianti", 0),
    "Artigiano con riduzione 35%": (60000, "Altre attività economiche", 5000, 15, "Artigiani e Commercianti", 35),
}

ricavi_default, settore_default, contributi_default, aliquota_default, cassa_default, riduzione_default = preset_values[preset]

col1, col2 = st.columns([1, 1.1])

with col1:
    st.header("📝 Parametri")
    ricavi = st.number_input("Ricavi annui (€)", min_value=0, max_value=85000, value=ricavi_default, step=1000)
    settore = st.selectbox("Settore di attività", list(SETTORI.keys()), index=list(SETTORI.keys()).index(settore_default))
    coefficiente = SETTORI[settore]

    contributi_prec = st.number_input(
        "Contributi versati anno precedente (€)",
        min_value=0,
        max_value=30000,
        value=contributi_default,
        step=500,
    )

    aliquota = st.radio("Aliquota imposta sostitutiva", [5, 15], index=0 if aliquota_default == 5 else 1)

    cassa = st.selectbox(
        "Cassa previdenziale",
        ["Gestione Separata INPS", "Artigiani e Commercianti"],
        index=0 if cassa_default == "Gestione Separata INPS" else 1,
    )

    riduzione = 0
    if cassa == "Artigiani e Commercianti":
        riduzione = st.selectbox(
            "Riduzione contributiva",
            [0, 35, 50],
            index=[0, 35, 50].index(riduzione_default if cassa_default == cassa else 0),
            format_func=lambda x: {0: "Nessuna", 35: "Riduzione 35%", 50: "Riduzione 50%"}[x],
        )

with col2:
    st.header("📈 Risultati")
    risultato = calcola_forfettario(ricavi, coefficiente, contributi_prec, aliquota, cassa, riduzione)

    st.metric("Netto annuo", f"€ {risultato['netto']:,.0f}")
    st.metric("Netto mensile", f"€ {risultato['netto']/12:,.0f}")
    st.metric("Tax rate effettivo", f"{risultato['tax_rate']:.2f}%")

    st.progress(min(100, int(risultato["tax_rate"])), text="Incidenza fiscale e contributiva")

    st.subheader("Breakdown")
    st.write(f"- Ricavi: **{euro(ricavi)}**")
    st.write(f"- Imposta sostitutiva: **{euro(risultato['imposta'])}**")
    st.write(f"- Contributi INPS: **{euro(risultato['contributi'])}**")
    st.write(f"- Totale imposte + contributi: **{euro(risultato['totale'])}**")

st.markdown("---")
st.subheader("🔁 Confronto scenario (what-if)")
col_a, col_b, col_c = st.columns(3)
with col_a:
    delta_ricavi = st.slider("Variazione ricavi", -20000, 20000, 5000, 1000)
with col_b:
    delta_contributi = st.slider("Variazione contributi deducibili", -5000, 5000, 0, 500)
with col_c:
    scenario_aliquota = st.selectbox("Aliquota scenario", [aliquota, 5 if aliquota == 15 else 15])

ricavi_whatif = max(0, ricavi + delta_ricavi)
contributi_whatif = max(0, contributi_prec + delta_contributi)
risultato_whatif = calcola_forfettario(
    ricavi_whatif,
    coefficiente,
    contributi_whatif,
    scenario_aliquota,
    cassa,
    riduzione,
)

c1, c2, c3 = st.columns(3)
c1.metric("Netto scenario", f"€ {risultato_whatif['netto']:,.0f}", delta=f"€ {risultato_whatif['netto'] - risultato['netto']:,.0f}")
c2.metric("Tax rate scenario", f"{risultato_whatif['tax_rate']:.2f}%", delta=f"{risultato_whatif['tax_rate'] - risultato['tax_rate']:.2f}%")
c3.metric("Totale oneri scenario", f"€ {risultato_whatif['totale']:,.0f}", delta=f"€ {risultato['totale'] - risultato_whatif['totale']:,.0f} risparmio")

st.info(
    "Simulazione indicativa a fini informativi. Verifica sempre con il tuo commercialista prima di decidere."
)
