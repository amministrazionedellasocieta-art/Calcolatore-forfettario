
import streamlit as st

# Configurazione pagina
st.set_page_config(
    page_title="Simulatore Forfettario 2025",
    page_icon="📊",
    layout="wide"
)

# Titolo
st.title("📊 Simulatore Regime Forfettario 2025")
st.markdown("**by Fisco Chiaro Consulting**")
st.markdown("---")

# Funzione di calcolo
def calcola_forfettario(ricavi, coefficiente, contributi_anno_prec, 
                        aliquota_imposta, tipo_cassa, riduzione_contrib=0):
    # Calcolo reddito imponibile
    reddito_imponibile_lordo = ricavi * (coefficiente / 100)
    reddito_imponibile_netto = reddito_imponibile_lordo - contributi_anno_prec

    # Calcolo imposta sostitutiva
    imposta_sostitutiva = reddito_imponibile_netto * (aliquota_imposta / 100)

    # Calcolo contributi
    if tipo_cassa == 'Gestione Separata INPS':
        aliquota_inps = 26.07
        contributi_inps = reddito_imponibile_lordo * (aliquota_inps / 100)
        riduzione_applicata = 0
    else:  # Artigiani/Commercianti
        contributo_fisso = 4460.64
        minimale = 18555
        eccedenza = max(0, reddito_imponibile_lordo - minimale)
        aliquota_eccedenza = 24

        if riduzione_contrib == 35:
            contributo_fisso = contributo_fisso * 0.65
            aliquota_eccedenza = aliquota_eccedenza * 0.65
            riduzione_applicata = 35
        elif riduzione_contrib == 50:
            contributo_fisso = contributo_fisso * 0.50
            aliquota_eccedenza = aliquota_eccedenza * 0.50
            riduzione_applicata = 50
        else:
            riduzione_applicata = 0

        contributi_variabili = eccedenza * (aliquota_eccedenza / 100)
        contributi_inps = contributo_fisso + contributi_variabili

    totale_imposte_contributi = imposta_sostitutiva + contributi_inps
    tax_rate = (totale_imposte_contributi / ricavi) * 100
    netto = ricavi - totale_imposte_contributi

    return {
        'reddito_lordo': reddito_imponibile_lordo,
        'reddito_netto': reddito_imponibile_netto,
        'imposta': imposta_sostitutiva,
        'contributi': contributi_inps,
        'totale': totale_imposte_contributi,
        'tax_rate': tax_rate,
        'netto': netto,
        'riduzione': riduzione_applicata
    }

# Layout a due colonne
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Parametri Input")

    # Input ricavi
    ricavi = st.number_input(
        "Ricavi annui (€)",
        min_value=0,
        max_value=85000,
        value=50000,
        step=1000,
        help="Inserisci il tuo fatturato annuo previsto"
    )

    # Coefficiente
    attivita = st.selectbox(
        "Settore di attività",
        [
            "Attività professionali, scientifiche, tecniche (78%)",
            "Costruzioni e attività immobiliari (86%)",
            "Intermediari commercio (62%)",
            "Commercio all'ingrosso e dettaglio (40%)",
            "Servizi alloggio e ristorazione (40%)",
            "Altre attività economiche (67%)"
        ]
    )

    # Estraggo il coefficiente
    coefficiente = int(attivita.split("(")[1].split("%")[0])

    # Contributi anno precedente
    contributi_prec = st.number_input(
        "Contributi versati anno precedente (€)",
        min_value=0,
        max_value=30000,
        value=5000,
        step=500,
        help="Contributi previdenziali deducibili"
    )

    # Aliquota
    aliquota = st.radio(
        "Aliquota imposta sostitutiva",
        [5, 15],
        format_func=lambda x: f"{x}% - {'Startup (primi 5 anni)' if x == 5 else 'Ordinaria'}",
        help="5% per nuove attività che rispettano i requisiti, 15% ordinaria"
    )

    # Tipo cassa
    cassa = st.selectbox(
        "Cassa previdenziale",
        ["Gestione Separata INPS", "Artigiani e Commercianti"]
    )

    # Riduzione contributiva (solo per Artigiani/Commercianti)
    riduzione = 0
    if cassa == "Artigiani e Commercianti":
        riduzione = st.selectbox(
            "Riduzione contributiva",
            [0, 35, 50],
            format_func=lambda x: {
                0: "Nessuna riduzione",
                35: "Riduzione 35% (da rinnovare annualmente)",
                50: "Riduzione 50% (nuove attività 2025, primi 36 mesi)"
            }[x],
            help="Le riduzioni sono disponibili solo per Artigiani/Commercianti"
        )
    else:
        st.info("ℹ️ La Gestione Separata NON prevede riduzioni contributive")

with col2:
    st.header("📊 Risultati")

    # Calcolo
    risultato = calcola_forfettario(
        ricavi, coefficiente, contributi_prec, 
        aliquota, cassa, riduzione
    )

    # Metriche principali
    st.metric(
        label="Tax Rate Effettivo",
        value=f"{risultato['tax_rate']:.2f}%",
        delta=None
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.metric(
            label="Netto Annuo",
            value=f"€ {risultato['netto']:,.0f}",
            delta=None
        )

    with col_b:
        st.metric(
            label="Netto Mensile",
            value=f"€ {risultato['netto']/12:,.0f}",
            delta=None
        )

    st.markdown("---")

    # Dettaglio calcoli
    st.subheader("Dettaglio Calcolo")

    st.write(f"**Reddito imponibile lordo:** € {risultato['reddito_lordo']:,.2f}")
    st.write(f"**Reddito imponibile netto:** € {risultato['reddito_netto']:,.2f}")
    st.write("")
    st.write(f"**Imposta sostitutiva ({aliquota}%):** € {risultato['imposta']:,.2f}")

    if riduzione > 0:
        st.write(f"**Contributi INPS (riduzione {riduzione}%):** € {risultato['contributi']:,.2f}")
    else:
        st.write(f"**Contributi INPS:** € {risultato['contributi']:,.2f}")

    st.write(f"**TOTALE imposte + contributi:** € {risultato['totale']:,.2f}")

# Footer con info
st.markdown("---")
st.info("""
**ℹ️ Note importanti:**
- **Aliquota 5%**: valida per 5 anni per nuove attività che non hanno esercitato attività analoghe nei 3 anni precedenti
- **Riduzione 35%**: riservata ad Artigiani/Commercianti forfettari, domanda entro 28 febbraio ogni anno
- **Riduzione 50%**: per nuove iscrizioni 2025 alla Gestione Artigiani/Commercianti, valida 36 mesi
- **Cumulabilità**: Aliquota 5% + Riduzione contributi sono cumulabili per il massimo risparmio fiscale
""")

st.markdown("---")
st.markdown("**Sviluppato da [Fisco Chiaro Consulting](https://fiscochiaro.it)** | © 2025")
