"""Fisco Digitale - fiscalita' e contabilita' per i lavori digitali.

Interfaccia Streamlit costruita sopra il pacchetto `fiscodigitale`: qui c'e'
solo presentazione, i calcoli stanno nei moduli e sono coperti da test.

Avvio:  streamlit run app_streamlit.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from fiscodigitale import (
    confronto as mod_confronto,
    contabilita,
    diagnosi,
    forfettario,
    iva_estero,
    parametri as P,
    previdenza,
    professioni,
    scadenze,
)

st.set_page_config(
    page_title="Fisco Digitale",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

EURO = "€ {:,.0f}"
COLORI_ESITO = {diagnosi.OK: "✅", diagnosi.ATTENZIONE: "⚠️", diagnosi.BLOCCANTE: "⛔"}


def euro(valore: float, decimali: int = 0) -> str:
    return f"€ {valore:,.{decimali}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def percentuale(valore: float, decimali: int = 1) -> str:
    return f"{valore * 100:.{decimali}f}%".replace(".", ",")


# ---------------------------------------------------------------------------
# SIDEBAR: il profilo di lavoro
# ---------------------------------------------------------------------------

st.sidebar.title("🧭 Il tuo profilo")

ricerca = st.sidebar.text_input(
    "Che lavoro fai?",
    placeholder="es. streamer, dropshipping, sviluppatore",
    help="Cerca per professione, piattaforma o codice ATECO",
)

if ricerca:
    trovate = professioni.cerca(ricerca, limite=12)
    if not trovate:
        st.sidebar.warning("Nessuna corrispondenza: scegli dall'elenco completo.")
        trovate = professioni.CATALOGO
else:
    categoria = st.sidebar.selectbox("Ambito", ("Tutti",) + professioni.CATEGORIE)
    trovate = (
        professioni.CATALOGO if categoria == "Tutti" else professioni.per_categoria(categoria)
    )

scelta = st.sidebar.selectbox(
    "Professione",
    trovate,
    format_func=lambda p: p.nome,
)

natura = None
if scelta.gestione_inps == professioni.DIPENDE:
    st.sidebar.warning(
        "Per questo lavoro l'inquadramento non e' scontato: cambia la cassa "
        "previdenziale e i contributi dovuti."
    )
    natura = st.sidebar.radio(
        "Come eserciti l'attivita'?",
        (diagnosi.PROFESSIONALE, diagnosi.IMPRESA),
        format_func=lambda x: {
            diagnosi.PROFESSIONALE: "Lavoro autonomo: conta soprattutto il mio apporto personale",
            diagnosi.IMPRESA: "Impresa: uso mezzi, personale o una struttura organizzata",
        }[x],
        index=None,
        help="Non dipende dal fatturato ma da come e' organizzata l'attivita'. "
             "Lascia vuoto per vedere il confronto tra le due forme.",
    )

st.sidebar.markdown("---")

ricavi = st.sidebar.number_input(
    "Ricavi annui attesi (€)", min_value=0, max_value=300_000, value=45_000, step=1_000
)
costi = st.sidebar.number_input(
    "Costi reali annui (€)",
    min_value=0,
    max_value=300_000,
    value=6_000,
    step=500,
    help="Attrezzatura, software, consulenze, pubblicita': nel forfettario non si "
         "deducono, ma li sostieni comunque.",
)
prima_attivita = st.sidebar.checkbox("Nuova attivita' (aliquota 5%)", value=True)
mesi = st.sidebar.slider("Mesi di attivita' nell'anno", 1, 12, 12)

with st.sidebar.expander("Altre fonti di ricavo"):
    st.caption(
        "Con piu' codici ATECO ogni attivita' usa il proprio coefficiente, ma il "
        "limite degli 85.000 euro si misura sulla somma dei ricavi."
    )
    altre_scelte = st.multiselect(
        "Aggiungi altre attivita'",
        [p for p in professioni.CATALOGO if p.slug != scelta.slug],
        format_func=lambda p: p.nome,
    )
    altre_attivita = []
    for altra in altre_scelte:
        ricavi_altra = st.number_input(
            f"Ricavi da {altra.nome} (€)",
            min_value=0,
            max_value=300_000,
            value=10_000,
            step=1_000,
            key=f"ricavi_{altra.slug}",
        )
        natura_altra = None
        if altra.gestione_inps == professioni.DIPENDE:
            natura_altra = st.radio(
                f"Natura di {altra.nome}",
                (diagnosi.PROFESSIONALE, diagnosi.IMPRESA),
                format_func=lambda x: "Professionale" if x == diagnosi.PROFESSIONALE else "Impresa",
                index=None,
                key=f"natura_{altra.slug}",
            )
        altre_attivita.append(
            diagnosi.AltraAttivita(altra.slug, float(ricavi_altra), natura_altra)
        )

with st.sidebar.expander("Come incassi"):
    clienti_esteri = st.checkbox("Fatturo a piattaforme o aziende estere", value=True)
    vendite_privati_ue = st.number_input(
        "Vendite annue a privati UE (€)", min_value=0, max_value=200_000, value=0, step=500
    )
    acquisti_esteri = st.number_input(
        "Acquisti annui di servizi esteri (€)",
        min_value=0,
        max_value=200_000,
        value=2_000,
        step=500,
        help="Pubblicita', software, commissioni delle piattaforme",
    )

with st.sidebar.expander("Requisiti e cause di esclusione"):
    redditi_dipendente = st.number_input(
        "Redditi da lavoro dipendente o pensione dell'anno scorso (€)",
        min_value=0,
        max_value=200_000,
        value=0,
        step=1_000,
    )
    partecipazioni = st.checkbox("Ho partecipazioni in societa' di persone o s.r.l. controllate")
    ex_datore = st.checkbox("Fatturo oltre il 50% al mio datore di lavoro attuale o recente")
    spese_personale = st.number_input(
        "Costo annuo di dipendenti e collaboratori (€)",
        min_value=0,
        max_value=100_000,
        value=0,
        step=1_000,
    )

with st.sidebar.expander("Previdenza"):
    prima_iscrizione_2025 = st.checkbox("Prima iscrizione INPS impresa nel 2025")
    riduzione = st.selectbox(
        "Riduzione contributiva richiesta",
        (0, 35, 50) if prima_iscrizione_2025 else (0, 35),
        format_func=lambda x: {
            0: "Nessuna",
            35: "35% - forfettari (domanda entro il 28 febbraio)",
            50: "50% - solo prima iscrizione 2025, per 36 mesi",
        }[x],
    )
    gia_assicurato = st.checkbox("Sono gia' assicurato altrove o pensionato")

profilo = diagnosi.Profilo(
    professione=scelta.slug,
    ricavi_attesi=float(ricavi),
    costi_annui=float(costi),
    prima_attivita=prima_attivita,
    mesi_attivita=mesi,
    redditi_dipendente_anno_precedente=float(redditi_dipendente),
    partecipazioni_societarie=partecipazioni,
    prevalenza_ex_datore=ex_datore,
    spese_personale=float(spese_personale),
    clienti_esteri_b2b=clienti_esteri,
    vendite_privati_ue=float(vendite_privati_ue),
    acquisti_servizi_esteri=float(acquisti_esteri),
    gia_assicurato_altrove=gia_assicurato,
    prima_iscrizione_2025=prima_iscrizione_2025,
    riduzione_richiesta=riduzione,
    natura_attivita=natura,
    altre_attivita=tuple(altre_attivita),
)

esame = diagnosi.analizza(profilo)

# ---------------------------------------------------------------------------
# TESTATA
# ---------------------------------------------------------------------------

st.title("🧭 Fisco Digitale")
st.caption(
    f"Fiscalita' e contabilita' dei lavori digitali · anno d'imposta {P.ANNO_IMPOSTA} · "
    f"{len(professioni.CATALOGO)} professioni mappate"
)

tab_diagnosi, tab_numeri, tab_iva, tab_conti, tab_scadenze, tab_catalogo = st.tabs(
    [
        "🩺 Diagnosi",
        "🧮 Numeri e confronto",
        "🌍 IVA e piattaforme",
        "📒 Contabilita'",
        "📅 Scadenze",
        "📚 Catalogo",
    ]
)

# ---------------------------------------------------------------------------
# TAB 1 - DIAGNOSI
# ---------------------------------------------------------------------------

with tab_diagnosi:
    if not esame.ammesso_al_forfettario:
        st.error("Con i dati indicati il regime forfettario non e' accessibile.")

    st.subheader(esame.professione.nome)
    st.write(esame.sintesi())

    c1, c2, c3, c4 = st.columns(4)
    if esame.multi_attivita:
        c1.metric("Codici ATECO", f"{len(esame.attivita)} attivita'")
        c2.metric("Coefficiente medio", percentuale(esame.coefficiente_medio, 1))
    else:
        c1.metric("Codice ATECO", esame.professione.ateco or "—")
        c2.metric("Coefficiente", f"{esame.professione.coefficiente_pct}%")
    c3.metric("Cassa previdenziale", diagnosi.previdenza_label(esame.gestione).replace("INPS", "").strip())
    c4.metric("Camera di Commercio", "Sì" if esame.professione.camera_commercio else "No")

    st.caption(esame.professione.ateco_descrizione)

    if esame.multi_attivita:
        st.markdown("### Le tue attivita'")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Attivita'": a.professione.nome,
                        "ATECO": a.professione.ateco or "—",
                        "Ricavi": a.ricavi,
                        "Coefficiente": f"{a.professione.coefficiente_pct}%",
                        "Reddito imponibile": a.reddito,
                        "Previdenza": diagnosi.previdenza_label(a.gestione),
                    }
                    for a in esame.attivita
                ]
            ).style.format({"Ricavi": lambda v: euro(v), "Reddito imponibile": lambda v: euro(v)}),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            f"Ricavi totali {euro(esame.ricavi_totali)} · reddito imponibile "
            f"{euro(esame.esito_forfettario.reddito_forfetario)} · coefficiente medio "
            f"{percentuale(esame.coefficiente_medio, 1)}. Il limite degli "
            f"{euro(P.SOGLIA_RICAVI)} si misura sulla somma; l'inquadramento "
            "previdenziale segue l'attivita' prevalente per ricavi."
        )
        if esame.contributi_doppia_iscrizione:
            st.warning(
                "Stai cumulando attivita' di natura diversa. Se INPS richiede "
                "l'iscrizione a entrambe le gestioni i contributi passano da "
                f"{euro(esame.esito_forfettario.contributi_dovuti)} a "
                f"{euro(esame.contributi_doppia_iscrizione)}."
            )

    if esame.inquadramento_da_scegliere and esame.costo_inquadramento:
        costo = esame.costo_inquadramento
        st.warning(
            "**Manca una scelta che cambia i numeri.** Questo lavoro puo' essere "
            "esercitato come libero professionista o come impresa, e non lo decide "
            "il fatturato: dipende da quanto pesano organizzazione e mezzi rispetto "
            "al tuo apporto personale. Indicalo nella barra laterale."
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Contributi da professionista", euro(costo["professionale"]))
        c2.metric("Contributi da impresa", euro(costo["impresa"]))
        c3.metric("Differenza", euro(abs(costo["differenza"])))
        st.caption(
            "I numeri qui sotto assumono la forma professionale. Da impresa si "
            "aggiungono l'iscrizione al Registro Imprese e una quota fissa dovuta "
            "anche in un anno senza incassi."
        )

    st.markdown("### Requisiti")
    for v in esame.verifiche:
        icona = COLORI_ESITO.get(v.esito, "•")
        with st.container():
            st.markdown(f"{icona} **{v.nome}** — {v.messaggio}")
            if v.riferimento:
                st.caption(v.riferimento)

    if esame.avvisi:
        st.markdown("### Da sapere")
        for a in esame.avvisi:
            st.warning(a)

    if esame.professione.note:
        st.markdown("### Note sull'inquadramento")
        for n in esame.professione.note:
            st.info(n)

    st.markdown("### Cosa devi fare, in ordine")
    for i, adempimento in enumerate(esame.adempimenti, start=1):
        titolo = f"{i}. {adempimento.titolo}"
        if not adempimento.obbligatorio:
            titolo += "  ·  consigliato"
        with st.expander(titolo):
            st.write(adempimento.descrizione)
            st.caption(f"Quando: {adempimento.quando}")
            if adempimento.costo_indicativo:
                st.caption(f"Costo indicativo: {adempimento.costo_indicativo}")

# ---------------------------------------------------------------------------
# TAB 2 - NUMERI
# ---------------------------------------------------------------------------

with tab_numeri:
    e = esame.esito_forfettario

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Netto annuo reale", euro(esame.netto_reale))
    c2.metric("Netto mensile", euro(esame.netto_reale / 12))
    c3.metric("Imposte e contributi", euro(e.totale_dovuto))
    c4.metric("Pressione effettiva", percentuale(e.pressione_effettiva))

    st.progress(
        min(1.0, e.pressione_effettiva),
        text=f"Su ogni 100 € fatturati, {percentuale(e.pressione_effettiva, 0)} "
             f"va tra imposta sostitutiva e INPS",
    )

    col_calcolo, col_grafico = st.columns([1, 1])

    with col_calcolo:
        st.markdown("#### Come si arriva al netto")
        righe = [
            ("Ricavi", e.ricavi),
            (
                f"Reddito forfetario ({percentuale(esame.coefficiente_medio, 1)}"
                + (" medio)" if esame.multi_attivita else ")"),
                e.reddito_forfetario,
            ),
            ("− Contributi dedotti", -e.contributi_dedotti),
            ("= Imponibile", e.imponibile),
            (f"− Imposta sostitutiva ({percentuale(e.aliquota, 0)})", -e.imposta_sostitutiva),
            ("− Contributi INPS dovuti", -e.contributi_dovuti),
            ("− Costi reali (non deducibili)", -profilo.costi_annui),
            ("− IVA estera indetraibile", -esame.iva_estera_annua),
            ("= Netto in tasca", esame.netto_reale),
        ]
        st.dataframe(
            pd.DataFrame(righe, columns=["Voce", "Importo"]).style.format(
                {"Importo": lambda v: euro(v, 2)}
            ),
            hide_index=True,
            width="stretch",
        )

        if e.contributi.riduzione_applicata:
            st.success(
                f"Riduzione contributiva del {e.contributi.riduzione_applicata}% applicata: "
                f"risparmi {euro(e.contributi.risparmio_riduzione)} l'anno."
            )
        for nota in e.contributi.note:
            st.caption(nota)

    with col_grafico:
        st.markdown("#### Dove finiscono i tuoi ricavi")
        ripartizione = pd.DataFrame(
            {
                "Voce": ["Netto", "Contributi INPS", "Imposta sostitutiva", "Costi reali", "IVA estera"],
                "Importo": [
                    max(0.0, esame.netto_reale),
                    e.contributi_dovuti,
                    e.imposta_sostitutiva,
                    profilo.costi_annui,
                    esame.iva_estera_annua,
                ],
            }
        )
        st.bar_chart(ripartizione.set_index("Voce"), horizontal=True)

        st.markdown("#### Quanto accantonare")
        st.metric(
            "Su ogni incasso metti da parte",
            percentuale(e.accantonamento_consigliato, 0),
            help="Include un margine per acconti e conguagli.",
        )

    st.markdown("---")
    st.markdown("### Forfettario o ordinario?")
    raffronto = esame.confronto_regimi
    c1, c2, c3 = st.columns(3)
    c1.metric("Netto in forfettario", euro(raffronto.netto_forfettario))
    c2.metric("Netto in ordinario", euro(raffronto.netto_ordinario))
    c3.metric(
        "Differenza",
        euro(abs(raffronto.differenza)),
        delta=("forfettario" if raffronto.conviene == "forfettario" else "ordinario"),
    )
    st.info(raffronto.sintesi)

    with st.expander("Come si compone il conto in regime ordinario"):
        o = raffronto.esito_ordinario
        righe_ord = [
            ("Ricavi", o.ricavi),
            ("− Costi deducibili", -o.costi),
            ("= Reddito", o.reddito),
            ("− Contributi (oneri deducibili)", -o.contributi_dovuti),
            ("= Imponibile IRPEF", o.imponibile_irpef),
            ("IRPEF lorda", o.irpef_lorda),
            ("− Detrazione lavoro autonomo", -o.detrazione),
            ("= IRPEF netta", o.irpef),
            ("+ Addizionali", o.addizionali),
        ]
        st.dataframe(
            pd.DataFrame(righe_ord, columns=["Voce", "Importo"]).style.format(
                {"Importo": lambda v: euro(v, 2)}
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(f"Aliquota marginale: {percentuale(o.aliquota_marginale, 0)}")
        for nota in o.note:
            st.caption(nota)

    if raffronto.costi_di_pareggio:
        curva = []
        passo = max(500, int(esame.ricavi_totali / 40)) if esame.ricavi_totali else 500
        for costo in range(0, int(esame.ricavi_totali) + 1, passo):
            c = mod_confronto.confronta(
                forfettario.Situazione(
                    ricavi=esame.ricavi_totali,
                    coefficiente=esame.coefficiente_medio,
                    gestione=esame.gestione,
                    startup=prima_attivita,
                    riduzione=e.contributi.riduzione_applicata,
                    mesi_attivita=mesi,
                ),
                costi=float(costo),
            )
            curva.append(
                {"Costi reali": costo, "Forfettario": c.netto_forfettario, "Ordinario": c.netto_ordinario}
            )
        st.line_chart(pd.DataFrame(curva).set_index("Costi reali"))
        st.caption(
            f"Le due curve si incrociano a {euro(raffronto.costi_di_pareggio)} di costi: "
            "oltre quel punto il forfettario ti fa perdere soldi."
        )

    st.markdown("---")
    st.markdown("### I primi tre anni di cassa")
    st.caption(
        "Competenza e cassa non coincidono: il primo anno si versa poco, il secondo "
        "arrivano insieme saldo e acconti. E' il motivo per cui tanti freelance si "
        "trovano scoperti a giugno."
    )
    piano = pd.DataFrame(
        [
            {
                "Anno": a.anno,
                "Ricavi": a.ricavi,
                "Imposta versata": a.imposta_cassa,
                "Contributi versati": a.contributi_cassa,
                "Uscite totali": a.uscite_cassa,
                "Resta in cassa": a.netto_di_cassa,
            }
            for a in esame.piano_cassa
        ]
    )
    st.dataframe(
        piano.style.format({c: lambda v: euro(v) for c in piano.columns if c != "Anno"}),
        hide_index=True,
        width="stretch",
    )
    for a in esame.piano_cassa:
        with st.expander(f"Dettaglio {a.anno}"):
            for d in a.dettaglio:
                st.write("· " + d)

    st.markdown("---")
    st.markdown("### Quanto devo fatturare per portare a casa una cifra?")
    obiettivo = st.number_input(
        "Netto desiderato all'anno (€)", min_value=0, max_value=200_000, value=30_000, step=1_000
    )
    if obiettivo:
        necessari = forfettario.ricavi_per_netto_obiettivo(
            float(obiettivo) + profilo.costi_annui + esame.iva_estera_annua,
            forfettario.Situazione(
                ricavi=esame.ricavi_totali or 1.0,
                coefficiente=esame.coefficiente_medio,
                gestione=esame.gestione,
                startup=prima_attivita,
                riduzione=e.contributi.riduzione_applicata,
                mesi_attivita=mesi,
            ),
        )
        st.success(
            f"Per {euro(obiettivo)} netti ti servono circa **{euro(necessari)}** di ricavi, "
            f"cioe' {euro(necessari / 12)} al mese."
        )
        if necessari > P.SOGLIA_RICAVI:
            st.warning(
                f"Sono oltre il limite di {euro(P.SOGLIA_RICAVI)} del forfettario: "
                "quell'obiettivo richiede un altro regime."
            )

# ---------------------------------------------------------------------------
# TAB 3 - IVA E PIATTAFORME
# ---------------------------------------------------------------------------

with tab_iva:
    st.markdown("### Come si fattura, caso per caso")
    st.caption(
        "Il lavoro digitale e' quasi sempre transfrontaliero. Qui trovi la regola "
        "applicabile, il documento da emettere e cosa scrivere in fattura."
    )

    for titolo, esito in esame.operazioni_iva:
        with st.expander(titolo, expanded=titolo.startswith("Fattura a un cliente italiano")):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**{esito.titolo}**")
                st.write(esito.iva)
                if esito.dicitura:
                    st.code(esito.dicitura, language=None)
            with c2:
                st.caption("Documento")
                st.write(esito.documento)
                if esito.natura:
                    st.caption(f"Natura: {esito.natura}")
                st.caption(esito.riferimento)
            if esito.adempimenti:
                st.markdown("**Adempimenti**")
                for a in esito.adempimenti:
                    st.write("· " + a)
            for r in esito.rischi:
                st.warning(r)

    st.markdown("---")
    st.markdown("### Analizza una singola operazione")
    c1, c2, c3, c4 = st.columns(4)
    direzione = c1.selectbox("Operazione", (iva_estero.VENDITA, iva_estero.ACQUISTO),
                             format_func=lambda x: "Emetto fattura" if x == iva_estero.VENDITA else "Ricevo fattura")
    oggetto = c2.selectbox(
        "Oggetto",
        (iva_estero.SERVIZIO, iva_estero.SERVIZIO_ELETTRONICO, iva_estero.BENE),
        format_func=lambda x: {
            iva_estero.SERVIZIO: "Servizio",
            iva_estero.SERVIZIO_ELETTRONICO: "Prodotto o servizio digitale",
            iva_estero.BENE: "Bene fisico",
        }[x],
    )
    controparte = c3.selectbox("Controparte", (iva_estero.B2B, iva_estero.B2C),
                               format_func=lambda x: "Azienda o piattaforma" if x == iva_estero.B2B else "Privato")
    area = c4.selectbox(
        "Dove si trova",
        (iva_estero.ITALIA, iva_estero.UE, iva_estero.EXTRA_UE),
        index=1,
        format_func=lambda x: {"IT": "Italia", "UE": "Unione Europea", "EXTRA_UE": "Extra-UE"}[x],
    )

    risultato = iva_estero.analizza(
        iva_estero.Operazione(
            direzione=direzione,
            oggetto=oggetto,
            controparte=controparte,
            area=area,
            regime=iva_estero.FORFETTARIO,
            vendite_ue_b2c_anno=float(vendite_privati_ue),
            acquisti_beni_ue_anno=0.0,
        )
    )
    st.success(f"**{risultato.titolo}** — {risultato.iva}")
    c1, c2 = st.columns(2)
    c1.write(f"**Documento:** {risultato.documento}")
    c1.caption(risultato.riferimento)
    if risultato.dicitura:
        c2.code(risultato.dicitura, language=None)
    for a in risultato.adempimenti:
        st.write("· " + a)
    for r in risultato.rischi:
        st.warning(r)

    st.markdown("---")
    st.markdown("### Le piattaforme e chi ti paga davvero")
    piattaforme_df = pd.DataFrame(
        [
            {
                "Piattaforma": p.nome,
                "Societa' che fattura": p.societa,
                "Area": p.area_label,
                "Ruolo": p.ruolo.capitalize(),
                "Ambito": p.categoria,
            }
            for p in iva_estero.PIATTAFORME
        ]
    )
    st.dataframe(piattaforme_df, hide_index=True, width="stretch")

    selezionata = st.selectbox(
        "Approfondisci una piattaforma",
        iva_estero.PIATTAFORME,
        format_func=lambda p: p.nome,
    )
    p, esito_p = iva_estero.analizza_piattaforma(selezionata.slug)
    st.info(f"**{p.nome}** — {p.societa} ({p.area_label})")
    st.write(f"**{esito_p.titolo}**: {esito_p.iva}")
    st.write(f"Documento: {esito_p.documento}")
    for n in p.note:
        st.write("· " + n)

    if acquisti_esteri:
        st.error(
            f"Sui tuoi {euro(acquisti_esteri)} di acquisti esteri annui maturi "
            f"{euro(iva_estero.iva_reverse_charge(float(acquisti_esteri)))} di IVA da "
            "versare con F24, che in forfettario non recuperi."
        )

# ---------------------------------------------------------------------------
# TAB 4 - CONTABILITA'
# ---------------------------------------------------------------------------

with tab_conti:
    st.markdown("### Registro incassi e spese")
    st.caption(
        "Registra i movimenti per vedere in tempo reale la distanza dalle soglie e "
        "quanto accantonare. I dati restano nella sessione del browser."
    )

    if "movimenti" not in st.session_state:
        st.session_state.movimenti = []

    with st.form("nuovo_movimento", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        m_data = c1.date_input("Data", value=date(P.ANNO_IMPOSTA, date.today().month, 1))
        m_descrizione = c2.text_input("Descrizione", placeholder="es. Sponsorizzazione brand")
        m_importo = c3.number_input("Importo (€)", min_value=0.0, step=100.0, value=1_000.0)
        c4, c5, c6 = st.columns(3)
        m_tipo = c4.selectbox("Tipo", (contabilita.INCASSO, contabilita.SPESA),
                              format_func=str.capitalize)
        m_area = c5.selectbox(
            "Controparte",
            (iva_estero.ITALIA, iva_estero.UE, iva_estero.EXTRA_UE),
            format_func=lambda x: {"IT": "Italia", "UE": "UE", "EXTRA_UE": "Extra-UE"}[x],
        )
        m_cliente = c6.selectbox("Tipo controparte", (iva_estero.B2B, iva_estero.B2C),
                                 format_func=lambda x: "Azienda" if x == iva_estero.B2B else "Privato")
        if st.form_submit_button("Aggiungi movimento", width="stretch"):
            if m_data.year != P.ANNO_IMPOSTA:
                st.error(f"Il registro copre l'anno {P.ANNO_IMPOSTA}.")
            else:
                st.session_state.movimenti.append(
                    contabilita.Movimento(
                        data=m_data,
                        descrizione=m_descrizione or "(senza descrizione)",
                        importo=float(m_importo),
                        tipo=m_tipo,
                        area=m_area,
                        controparte=m_cliente,
                    )
                )

    registro = contabilita.Registro(P.ANNO_IMPOSTA, list(st.session_state.movimenti))

    if registro.movimenti:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Incassato", euro(registro.incassi))
        c2.metric("Speso", euro(registro.spese))
        c3.metric("Proiezione a fine anno", euro(registro.proiezione_annuale()))
        c4.metric("IVA estera maturata", euro(registro.iva_reverse_charge_maturata, 2))

        for allerta in registro.allerte(costo_personale=float(spese_personale)):
            if allerta.startswith("[SUPERATA]"):
                st.error(allerta)
            elif allerta.startswith("[IVA]"):
                st.info(allerta)
            else:
                st.warning(allerta)

        st.markdown("#### Soglie")
        for soglia in registro.soglie(costo_personale=float(spese_personale)):
            st.write(f"**{soglia.nome}** — {euro(soglia.valore_corrente)} su {euro(soglia.limite)}")
            st.progress(min(1.0, soglia.percentuale))
            st.caption(f"{soglia.descrizione} {soglia.conseguenza}")

        accantonamento = registro.accantonamento(
            forfettario.Situazione(
                ricavi=max(registro.incassi, 1.0),
                coefficiente=esame.coefficiente_medio,
                gestione=esame.gestione,
                startup=prima_attivita,
                riduzione=e.contributi.riduzione_applicata,
                mesi_attivita=mesi,
            )
        )
        st.markdown("#### Accantonamento")
        c1, c2, c3 = st.columns(3)
        c1.metric("Quota su ogni incasso", percentuale(accantonamento["quota_su_ogni_incasso"]))
        c2.metric("Da avere gia' da parte", euro(accantonamento["da_accantonare_ora"]))
        c3.metric("IVA estera da versare", euro(accantonamento["iva_estera_da_versare"], 2))

        st.markdown("#### Movimenti")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Data": m.data,
                        "Descrizione": m.descrizione,
                        "Tipo": m.tipo.capitalize(),
                        "Area": m.area,
                        "Importo": m.importo,
                        "IVA reverse charge": m.iva_reverse_charge,
                    }
                    for m in sorted(registro.movimenti, key=lambda x: x.data)
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        andamento = pd.DataFrame(
            {"Mese": list(registro.incassi_per_mese().keys()),
             "Incassi": list(registro.incassi_per_mese().values())}
        ).set_index("Mese")
        st.bar_chart(andamento)

        if st.button("Svuota il registro"):
            st.session_state.movimenti = []
            st.rerun()
    else:
        st.info("Aggiungi il primo movimento per vedere soglie, proiezioni e accantonamento.")

# ---------------------------------------------------------------------------
# TAB 5 - SCADENZE
# ---------------------------------------------------------------------------

with tab_scadenze:
    st.markdown("### Le tue scadenze")
    st.caption("Filtrate in base al regime, alla cassa previdenziale e alle operazioni estere.")

    profilo_scadenze = scadenze.Profilo(
        regime="forfettario",
        gestione=esame.gestione,
        acquisti_esteri=acquisti_esteri > 0,
        vendite_ue_b2b=clienti_esteri,
        riduzione_contributiva_da_chiedere=esame.gestione in previdenza.GESTIONI_IMPRESA,
        oss=vendite_privati_ue > P.SOGLIA_OSS,
    )

    st.markdown("#### Prossime")
    for s in scadenze.prossime(6, profilo=profilo_scadenze):
        giorni = s.giorni_mancanti()
        etichetta = "oggi" if giorni == 0 else f"tra {giorni} giorni"
        with st.container():
            st.markdown(f"**{s.data.strftime('%d/%m/%Y')}** · {s.titolo} — _{etichetta}_")
            st.caption(f"{s.categoria} · {s.descrizione}")

    st.markdown("---")
    st.markdown(f"#### Calendario {P.ANNO_IMPOSTA}")
    tutte = scadenze.calendario(P.ANNO_IMPOSTA, profilo_scadenze)
    categorie = sorted({s.categoria for s in tutte})
    filtro = st.multiselect("Categorie", categorie, default=categorie)
    calendario_df = pd.DataFrame(
        [
            {"Data": s.data, "Scadenza": s.titolo, "Categoria": s.categoria, "Dettaglio": s.descrizione}
            for s in tutte
            if s.categoria in filtro
        ]
    )
    st.dataframe(calendario_df, hide_index=True, width="stretch", height=420)

# ---------------------------------------------------------------------------
# TAB 6 - CATALOGO
# ---------------------------------------------------------------------------

with tab_catalogo:
    st.markdown("### Le professioni digitali e il loro inquadramento")
    st.caption(
        "Coefficienti secondo l'Allegato 4 della L. 190/2014, codici aggiornati alla "
        "classificazione ATECO 2025."
    )
    catalogo_df = pd.DataFrame(
        [
            {
                "Professione": p.nome,
                "Ambito": p.categoria,
                "ATECO": p.ateco or "—",
                "Descrizione ATECO": p.ateco_descrizione,
                "Coefficiente": f"{p.coefficiente_pct}%",
                "Previdenza": p.gestione_label,
                "Camera di Commercio": "Sì" if p.camera_commercio else "No",
            }
            for p in professioni.CATALOGO
        ]
    )
    filtro_cat = st.multiselect("Filtra per ambito", professioni.CATEGORIE)
    if filtro_cat:
        catalogo_df = catalogo_df[catalogo_df["Ambito"].isin(filtro_cat)]
    st.dataframe(catalogo_df, hide_index=True, width="stretch", height=560)

    st.markdown("#### Coefficienti di redditivita' per gruppo")
    st.dataframe(
        pd.DataFrame(
            [
                {"Gruppo": descrizione, "Coefficiente": f"{int(valore * 100)}%"}
                for valore, descrizione in P.COEFFICIENTI.values()
            ]
        ),
        hide_index=True,
        width="stretch",
    )

# ---------------------------------------------------------------------------
# PIEDE
# ---------------------------------------------------------------------------

st.markdown("---")
with st.expander("Fonti e limiti dello strumento"):
    st.write(
        "Le regole implementate sono aggiornate all'anno d'imposta "
        f"{P.ANNO_IMPOSTA}. Riferimenti principali:"
    )
    for chiave, fonte in P.FONTI.items():
        st.write(f"· **{chiave.replace('_', ' ').capitalize()}**: {fonte}")
    st.warning(
        "Lo strumento fornisce stime e orientamento, non sostituisce il parere di un "
        "commercialista. L'inquadramento corretto dipende da come l'attivita' e' "
        "organizzata in concreto, e i codici ATECO vanno confermati caso per caso."
    )
