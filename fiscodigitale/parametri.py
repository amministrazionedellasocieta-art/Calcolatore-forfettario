"""Parametri fiscali, previdenziali e IVA per l'anno d'imposta 2026.

Unico punto di verita' del progetto: tutti i motori di calcolo leggono da qui.
Ogni valore riporta la fonte, cosi' l'aggiornamento annuale e' una modifica
localizzata a questo file (e ai test che lo presidiano).

ATTENZIONE: i valori vanno riverificati ad ogni circolare INPS di inizio anno
e ad ogni legge di bilancio.
"""

from __future__ import annotations

ANNO_IMPOSTA = 2026

FONTI = {
    "forfettario": "L. 190/2014 art. 1 c. 54-89; Legge di Bilancio 2026",
    "coefficienti": "Allegato 4 L. 190/2014 (da ultimo sostituito da L. 145/2018)",
    "gestione_separata": "Circolare INPS n. 8 del 03/02/2026",
    "artigiani_commercianti": "Circolare INPS n. 14 del 2026",
    "irpef": "art. 11 TUIR come modificato dalla Legge di Bilancio 2026",
    "cripto": "art. 67 c. 1 lett. c-sexies TUIR; L. 207/2024 art. 1 c. 25-29",
    "iva_estero": "DPR 633/72 artt. 7-ter, 17 c. 2, 21; Dir. 2006/112/CE",
}

# ---------------------------------------------------------------------------
# REGIME FORFETTARIO
# ---------------------------------------------------------------------------

SOGLIA_RICAVI = 85_000.0            # limite di permanenza (verifica a fine anno)
SOGLIA_USCITA_IMMEDIATA = 100_000.0  # oltre: uscita dal regime nello stesso anno
SOGLIA_REDDITI_DIPENDENTE = 35_000.0  # redditi da lavoro dipendente/pensione anno prec.
LIMITE_SPESE_PERSONALE = 20_000.0    # costo lordo lavoro dipendente/accessorio

ALIQUOTA_SOSTITUTIVA = 0.15
ALIQUOTA_SOSTITUTIVA_STARTUP = 0.05
ANNI_ALIQUOTA_STARTUP = 5

# Il forfettario non e' sostituto d'imposta e non subisce ritenuta d'acconto.
RITENUTA_ACCONTO_ORDINARIA = 0.20

# Bollo sulle fatture senza IVA di importo superiore alla soglia.
IMPOSTA_BOLLO = 2.00
SOGLIA_BOLLO = 77.47

# Acconti imposta sostitutiva (stesse regole IRPEF).
ACCONTO_SOGLIA_MINIMA = 51.65      # sotto questo importo l'acconto non e' dovuto
ACCONTO_PERCENTUALE = 1.00         # 100% dell'imposta dell'anno precedente
ACCONTO_UNICA_RATA_SOTTO = 257.52  # sotto: unica rata a novembre
ACCONTO_PRIMA_RATA = 0.40
ACCONTO_SECONDA_RATA = 0.60

# Coefficienti di redditivita' per gruppo di attivita'.
# NB: la tabella e' ancora agganciata ai gruppi ATECO 2007; con ATECO 2025 si
# applica il coefficiente dell'attivita' corrispondente finche' non esce la
# nuova tabella.
COEFFICIENTI = {
    "industrie_alimentari": (0.40, "Industrie alimentari e delle bevande (10-11)"),
    "commercio": (0.40, "Commercio all'ingrosso e al dettaglio (45, 46.1, 46.3, 46.5, 46.9, 47.x)"),
    "commercio_ambulante_alimentari": (0.40, "Commercio ambulante di alimentari e bevande (47.81)"),
    "commercio_ambulante_altro": (0.54, "Commercio ambulante di altri prodotti (47.82, 47.89)"),
    "costruzioni_immobiliare": (0.86, "Costruzioni e attivita' immobiliari (41-43, 68)"),
    "intermediari": (0.62, "Intermediari del commercio (46.1)"),
    "alloggio_ristorazione": (0.40, "Servizi di alloggio e ristorazione (55-56)"),
    "professionale": (0.78, "Attivita' professionali, scientifiche, tecniche, sanitarie, "
                            "istruzione, servizi finanziari e assicurativi (64-66, 69-75, 85-88)"),
    "altre_attivita": (0.67, "Altre attivita' economiche (tutti gli altri codici)"),
}

# ---------------------------------------------------------------------------
# PREVIDENZA
# ---------------------------------------------------------------------------

GESTIONE_SEPARATA = {
    "aliquota_professionisti": 0.2607,   # 25% IVS + 0,72% + 0,35% ISCRO
    "aliquota_gia_assicurati": 0.24,     # pensionati o iscritti ad altra gestione
    "minimale_accredito": 18_808.0,      # soglia per l'accredito dell'anno intero
    "massimale": 122_295.0,
    "riparto_committente": 2 / 3,        # solo co.co.co: 2/3 committente, 1/3 lavoratore
}

ARTIGIANI = {
    "contributo_fisso": 4_521.36,   # comprensivo di maternita'
    "aliquota_ivs": 0.24,
    "aliquota_ivs_oltre_scaglione": 0.25,
}

COMMERCIANTI = {
    "contributo_fisso": 4_611.64,   # comprensivo di maternita' e 0,48% L. 193/2000
    "aliquota_ivs": 0.2448,
    "aliquota_ivs_oltre_scaglione": 0.2548,
}

MINIMALE_ARTIGIANI_COMMERCIANTI = 18_808.0
SCAGLIONE_ARTIGIANI_COMMERCIANTI = 56_224.0
MASSIMALE_ARTIGIANI_COMMERCIANTI = 122_295.0  # iscritti dal 1996; ante-1996 piu' basso
CONTRIBUTO_MATERNITA = 7.44

# Riduzioni contributive per artigiani e commercianti.
RIDUZIONE_35 = 0.35   # forfettari, domanda entro il 28 febbraio, su tutta la contribuzione
RIDUZIONE_50 = 0.50   # prima iscrizione nel 2025, 36 mesi, solo sulla quota IVS
RIDUZIONE_50_APERTA_A_NUOVE_ISCRIZIONI = False  # chiusa dal 01/01/2026

# Casse professionali: parametri indicativi, ogni cassa ha regolamento proprio.
CASSE_PROFESSIONALI = {
    "nessuna": ("Nessuna cassa (Gestione Separata)", 0.0, 0.0),
    "inarcassa": ("Inarcassa (ingegneri e architetti)", 0.145, 0.04),
    "cnpadc": ("CNPADC (dottori commercialisti)", 0.12, 0.04),
    "enpacl": ("ENPACL (consulenti del lavoro)", 0.12, 0.04),
    "cassa_forense": ("Cassa Forense (avvocati)", 0.16, 0.04),
}

# ---------------------------------------------------------------------------
# REGIME ORDINARIO / SEMPLIFICATO
# ---------------------------------------------------------------------------

SCAGLIONI_IRPEF = (
    (28_000.0, 0.23),
    (50_000.0, 0.33),
    (float("inf"), 0.43),
)

ADDIZIONALE_REGIONALE_MEDIA = 0.0173
ADDIZIONALE_COMUNALE_MEDIA = 0.0060

# Deduzioni/detrazioni minime usate nel confronto (semplificazione dichiarata).
DETRAZIONE_LAVORO_AUTONOMO_MAX = 1_265.0
NO_TAX_AREA_AUTONOMI = 5_500.0

IRAP_ALIQUOTA_ORDINARIA = 0.039  # dovuta solo con autonoma organizzazione

# ---------------------------------------------------------------------------
# IVA E OPERAZIONI CON L'ESTERO
# ---------------------------------------------------------------------------

IVA_ORDINARIA = 0.22
SOGLIA_OSS = 10_000.0          # vendite a distanza + servizi TTE B2C verso UE
GIORNI_EMISSIONE_FATTURA = 12
GIORNO_AUTOFATTURA_ACQUISTI = 15  # entro il 15 del mese successivo
GIORNO_VERSAMENTO_IVA_REVERSE = 16  # F24, mese successivo

CODICI_DOCUMENTO = {
    "TD01": "Fattura",
    "TD17": "Integrazione/autofattura per acquisto di SERVIZI dall'estero",
    "TD18": "Integrazione per acquisto di BENI intracomunitari",
    "TD19": "Integrazione/autofattura per acquisto di beni ex art. 17 c. 2 (beni gia' in Italia)",
}

NATURE_IVA = {
    "N2.1": "Non soggetta ad IVA ai sensi degli artt. da 7 a 7-septies DPR 633/72",
    "N2.2": "Operazione non soggetta - altri casi",
    "N3.2": "Non imponibile - cessioni intracomunitarie",
    "N3.1": "Non imponibile - esportazioni",
}

# ---------------------------------------------------------------------------
# CRIPTO-ATTIVITA'
# ---------------------------------------------------------------------------

CRIPTO = {
    "aliquota_plusvalenze": 0.33,        # dal 01/01/2026
    "aliquota_emt_micar": 0.26,          # token di moneta elettronica ancorati all'euro
    "soglia_esenzione": 0.0,             # abolita
    "imposta_valore_cripto": 0.002,      # 2 per mille sul valore, tipo bollo
    "quadro_dichiarativo": "Quadro W (RW nel modello Redditi PF)",
}

# ---------------------------------------------------------------------------
# ALTRE SOGLIE UTILI AL LAVORO DIGITALE
# ---------------------------------------------------------------------------

SOGLIA_PRESTAZIONE_OCCASIONALE_INPS = 5_000.0   # oltre: iscrizione Gestione Separata
SOGLIA_DIRITTO_AUTORE_ABBATTIMENTO = 0.25       # 40% se under 35
ETA_ABBATTIMENTO_MAGGIORE = 35
ABBATTIMENTO_DIRITTO_AUTORE_UNDER35 = 0.40
