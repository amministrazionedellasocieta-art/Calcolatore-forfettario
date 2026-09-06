"""Diagnosi fiscale completa a partire dal lavoro reale.

E' il modulo che tiene insieme gli altri: si parte da "faccio lo streamer e
prevedo 40.000 euro", si arriva a inquadramento, verifica dei requisiti,
numeri, adempimenti e scadenze. Il ragionamento che un commercialista fa alla
prima consulenza, reso ripetibile.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date

from . import confronto, forfettario, iva_estero
from . import parametri as P
from . import previdenza, professioni, scadenze

OK = "ok"
ATTENZIONE = "attenzione"
BLOCCANTE = "bloccante"


@dataclass(frozen=True)
class Verifica:
    nome: str
    esito: str
    messaggio: str
    riferimento: str = ""


@dataclass(frozen=True)
class Adempimento:
    titolo: str
    descrizione: str
    quando: str
    obbligatorio: bool = True
    costo_indicativo: str = ""


@dataclass(frozen=True)
class Profilo:
    """Come lavori davvero."""

    professione: str
    ricavi_attesi: float
    costi_annui: float = 0.0
    prima_attivita: bool = True
    mesi_attivita: int = 12
    gestione_scelta: str | None = None
    # Cause di esclusione e requisiti
    redditi_dipendente_anno_precedente: float = 0.0
    partecipazioni_societarie: bool = False
    prevalenza_ex_datore: bool = False
    residente_estero: bool = False
    spese_personale: float = 0.0
    # Come incassi
    clienti_esteri_b2b: bool = False
    vendite_privati_ue: float = 0.0
    acquisti_servizi_esteri: float = 0.0
    # Contributi
    gia_assicurato_altrove: bool = False
    prima_iscrizione_2025: bool = False
    riduzione_richiesta: int = 0

    def __post_init__(self) -> None:
        if self.ricavi_attesi < 0:
            raise ValueError("i ricavi attesi non possono essere negativi")


@dataclass(frozen=True)
class Diagnosi:
    profilo: Profilo
    professione: professioni.Professione
    gestione: str
    verifiche: tuple[Verifica, ...]
    esito_forfettario: forfettario.Esito
    confronto_regimi: confronto.Confronto
    piano_cassa: tuple[forfettario.AnnoDiCassa, ...]
    adempimenti: tuple[Adempimento, ...]
    operazioni_iva: tuple[tuple[str, iva_estero.EsitoIva], ...]
    prossime_scadenze: tuple[scadenze.Scadenza, ...]
    avvisi: tuple[str, ...]

    @property
    def ammesso_al_forfettario(self) -> bool:
        return not any(v.esito == BLOCCANTE for v in self.verifiche)

    @property
    def iva_estera_annua(self) -> float:
        return iva_estero.iva_reverse_charge(self.profilo.acquisti_servizi_esteri)

    @property
    def netto_reale(self) -> float:
        """Netto dopo imposte, contributi, costi reali e IVA estera indetraibile."""
        return round(
            self.esito_forfettario.netto
            - self.profilo.costi_annui
            - self.iva_estera_annua,
            2,
        )

    def sintesi(self) -> str:
        if not self.ammesso_al_forfettario:
            return (
                f"{self.professione.nome}: con i dati indicati il regime forfettario "
                "non e' accessibile. Il calcolo mostra comunque il confronto con "
                "l'ordinario."
            )
        return (
            f"{self.professione.nome} - ATECO {self.professione.ateco}, coefficiente "
            f"{self.professione.coefficiente_pct}%, {previdenza_label(self.gestione)}. "
            f"Su {self.profilo.ricavi_attesi:,.0f} euro di ricavi versi "
            f"{self.esito_forfettario.totale_dovuto:,.0f} euro tra imposta e contributi "
            f"({self.esito_forfettario.pressione_effettiva * 100:.1f}%) e ne restano "
            f"{self.netto_reale:,.0f} netti."
        )


def previdenza_label(gestione: str) -> str:
    return professioni.LABEL_GESTIONE.get(gestione, gestione)


def _gestione_effettiva(prof: professioni.Professione, profilo: Profilo) -> str:
    if profilo.gestione_scelta:
        return profilo.gestione_scelta
    mappa = {
        professioni.GS: previdenza.GESTIONE_SEPARATA,
        professioni.COMMERCIANTI: previdenza.COMMERCIANTI,
        professioni.ARTIGIANI: previdenza.ARTIGIANI,
        professioni.NESSUNO: previdenza.NESSUNA,
    }
    # Quando l'inquadramento dipende dal modo in cui lavori, si assume la
    # forma piu' diffusa: professionale sotto i 30.000 euro, d'impresa sopra.
    if prof.gestione_inps == professioni.DIPENDE:
        return (
            previdenza.COMMERCIANTI
            if prof.camera_commercio and profilo.ricavi_attesi >= 30_000
            else previdenza.GESTIONE_SEPARATA
        )
    return mappa[prof.gestione_inps]


def _verifiche(profilo: Profilo, prof: professioni.Professione) -> tuple[Verifica, ...]:
    v: list[Verifica] = []
    soglia_ragguagliata = P.SOGLIA_RICAVI * profilo.mesi_attivita / 12

    if profilo.ricavi_attesi > P.SOGLIA_USCITA_IMMEDIATA:
        v.append(Verifica(
            "Limite dei ricavi", BLOCCANTE,
            f"Ricavi previsti di {profilo.ricavi_attesi:,.0f} euro: oltre "
            f"{P.SOGLIA_USCITA_IMMEDIATA:,.0f} euro il regime decade nell'anno stesso.",
            "art. 1 c. 71 L. 190/2014",
        ))
    elif profilo.ricavi_attesi > soglia_ragguagliata:
        v.append(Verifica(
            "Limite dei ricavi", ATTENZIONE,
            f"Ricavi previsti di {profilo.ricavi_attesi:,.0f} euro contro un limite di "
            f"{soglia_ragguagliata:,.0f}: userai il forfettario quest'anno e passerai "
            "all'ordinario dal prossimo.",
            "art. 1 c. 54 L. 190/2014",
        ))
    else:
        v.append(Verifica(
            "Limite dei ricavi", OK,
            f"{profilo.ricavi_attesi:,.0f} euro su un limite di {soglia_ragguagliata:,.0f}: "
            f"hai ancora {soglia_ragguagliata - profilo.ricavi_attesi:,.0f} euro di margine.",
        ))

    if profilo.redditi_dipendente_anno_precedente > P.SOGLIA_REDDITI_DIPENDENTE:
        v.append(Verifica(
            "Redditi da lavoro dipendente", BLOCCANTE,
            f"Nell'anno precedente hai percepito "
            f"{profilo.redditi_dipendente_anno_precedente:,.0f} euro da lavoro dipendente "
            f"o pensione, oltre il limite di {P.SOGLIA_REDDITI_DIPENDENTE:,.0f}. "
            "Il limite non opera se il rapporto di lavoro e' cessato.",
            "art. 1 c. 57 lett. d-ter L. 190/2014",
        ))
    elif profilo.redditi_dipendente_anno_precedente > 0:
        v.append(Verifica(
            "Redditi da lavoro dipendente", OK,
            f"{profilo.redditi_dipendente_anno_precedente:,.0f} euro sotto il limite di "
            f"{P.SOGLIA_REDDITI_DIPENDENTE:,.0f} euro: puoi cumulare lavoro dipendente e "
            "partita IVA forfettaria.",
        ))

    if profilo.partecipazioni_societarie:
        v.append(Verifica(
            "Partecipazioni societarie", BLOCCANTE,
            "Le partecipazioni in societa' di persone o il controllo di una s.r.l. che "
            "svolge attivita' riconducibile alla tua escludono il regime.",
            "art. 1 c. 57 lett. d L. 190/2014",
        ))

    if profilo.prevalenza_ex_datore:
        v.append(Verifica(
            "Fatturato verso l'ex datore di lavoro", BLOCCANTE,
            "Oltre il 50% dei ricavi verso il datore di lavoro attuale o dei due anni "
            "precedenti: il regime e' precluso.",
            "art. 1 c. 57 lett. d-bis L. 190/2014",
        ))

    if profilo.spese_personale > P.LIMITE_SPESE_PERSONALE:
        v.append(Verifica(
            "Spese per il personale", BLOCCANTE,
            f"{profilo.spese_personale:,.0f} euro di costi per dipendenti e "
            f"collaboratori, oltre il limite di {P.LIMITE_SPESE_PERSONALE:,.0f}.",
            "art. 1 c. 54 lett. b L. 190/2014",
        ))

    if profilo.residente_estero:
        v.append(Verifica(
            "Residenza fiscale", ATTENZIONE,
            "Da non residente il regime e' ammesso solo se risiedi in uno Stato UE o SEE "
            "e produci in Italia almeno il 75% del reddito complessivo.",
            "art. 1 c. 57 lett. b L. 190/2014",
        ))

    if profilo.prima_attivita:
        v.append(Verifica(
            "Aliquota agevolata al 5%", OK,
            f"Se non hai svolto la stessa attivita' nei 3 anni precedenti, per "
            f"{P.ANNI_ALIQUOTA_STARTUP} anni l'imposta e' al "
            f"{P.ALIQUOTA_SOSTITUTIVA_STARTUP * 100:.0f}% invece che al "
            f"{P.ALIQUOTA_SOSTITUTIVA * 100:.0f}%.",
            "art. 1 c. 65 L. 190/2014",
        ))

    return tuple(v)


def _adempimenti(profilo: Profilo, prof: professioni.Professione, gestione: str) -> tuple[Adempimento, ...]:
    lista: list[Adempimento] = [
        Adempimento(
            "Apertura della partita IVA",
            f"Codice ATECO {prof.ateco} ({prof.ateco_descrizione}). "
            + (
                "Attivita' d'impresa: si presenta la ComUnica al Registro Imprese, che "
                "attiva insieme Agenzia delle Entrate, INPS e Camera di Commercio."
                if prof.camera_commercio
                else "Attivita' professionale: si presenta il modello AA9/12 "
                     "all'Agenzia delle Entrate, gratuitamente e senza intermediari."
            ),
            "Prima di iniziare l'attivita' o entro 30 giorni",
            costo_indicativo="Gratuito" if not prof.camera_commercio else "Circa 150-250 euro di diritti e bolli",
        ),
    ]

    if prof.camera_commercio:
        lista.append(Adempimento(
            "Iscrizione al Registro Imprese e SCIA",
            "L'esercizio in forma d'impresa richiede l'iscrizione alla Camera di "
            "Commercio e, per il commercio, la SCIA al SUAP del Comune.",
            "Contestuale all'apertura",
            costo_indicativo="Diritto annuale camerale di circa 53-120 euro",
        ))

    if gestione in previdenza.GESTIONI_IMPRESA:
        lista.append(Adempimento(
            "Iscrizione alla Gestione Artigiani o Commercianti",
            "Comporta contributi fissi trimestrali dovuti anche a reddito zero "
            f"(circa {P.COMMERCIANTI['contributo_fisso']:,.0f} euro l'anno). "
            "Chiedi la riduzione del 35% entro il 28 febbraio.",
            "Contestuale all'apertura",
        ))
    elif gestione == previdenza.GESTIONE_SEPARATA:
        lista.append(Adempimento(
            "Iscrizione alla Gestione Separata INPS",
            f"Aliquota del {P.GESTIONE_SEPARATA['aliquota_professionisti'] * 100:.2f}% "
            "sul reddito, senza contributi minimi. Il primo versamento cade a giugno "
            "dell'anno successivo: e' il momento in cui molti si trovano scoperti.",
            "Entro l'inizio dell'attivita'",
            costo_indicativo="Gratuita",
        ))

    lista.append(Adempimento(
        "Canale per la fatturazione elettronica",
        "Serve un codice destinatario o una PEC per ricevere le fatture, e un software "
        "per emetterle. La fattura elettronica e' obbligatoria anche in forfettario.",
        "Prima della prima fattura",
        costo_indicativo="Da 0 a 100 euro l'anno",
    ))

    if profilo.clienti_esteri_b2b:
        lista.append(Adempimento(
            "Iscrizione al VIES",
            "Obbligatoria per fatturare servizi a imprese UE senza IVA. Si richiede "
            "nel modello di apertura o successivamente dal cassetto fiscale; "
            "l'iscrizione e' effettiva dal giorno stesso.",
            "Prima della prima fattura estera",
        ))
        lista.append(Adempimento(
            "Elenchi INTRASTAT dei servizi resi",
            "Riepilogo periodico dei servizi resi a soggetti passivi UE.",
            "Entro il 25 del mese successivo al periodo",
            obbligatorio=True,
        ))

    if profilo.acquisti_servizi_esteri > 0:
        iva_annua = iva_estero.iva_reverse_charge(profilo.acquisti_servizi_esteri)
        lista.append(Adempimento(
            "Inversione contabile sugli acquisti esteri",
            f"Su {profilo.acquisti_servizi_esteri:,.0f} euro di servizi esteri (pubblicita', "
            f"software, commissioni) devi integrare le fatture e versare "
            f"{iva_annua:,.0f} euro di IVA che nel forfettario non recuperi.",
            f"TD17 entro il {P.GIORNO_AUTOFATTURA_ACQUISTI} e F24 entro il "
            f"{P.GIORNO_VERSAMENTO_IVA_REVERSE} del mese successivo",
            costo_indicativo=f"{iva_annua:,.0f} euro l'anno di IVA indetraibile",
        ))

    if profilo.vendite_privati_ue > P.SOGLIA_OSS:
        lista.append(Adempimento(
            "Valutazione del regime OSS",
            f"Le vendite a privati UE ({profilo.vendite_privati_ue:,.0f} euro) superano "
            f"la soglia di {P.SOGLIA_OSS:,.0f} euro: si applica l'IVA del Paese del "
            "cliente. Per un forfettario e' un passaggio da impostare con un professionista.",
            "Prima di superare la soglia",
        ))

    lista.append(Adempimento(
        "Imposta di bollo sulle fatture",
        f"Bollo da {P.IMPOSTA_BOLLO:.2f} euro su ogni fattura senza IVA superiore a "
        f"{P.SOGLIA_BOLLO:.2f} euro. Puoi riaddebitarlo al cliente, ma resta un tuo ricavo.",
        "Versamento trimestrale",
    ))

    lista.append(Adempimento(
        "Registro degli incassi e conto dedicato",
        "Il forfettario non tiene la contabilita', ma deve documentare i ricavi. Un "
        "conto separato e un registro aggiornato evitano contestazioni e rendono "
        "leggibile la posizione rispetto alle soglie.",
        "Continuativo",
        obbligatorio=False,
    ))

    return tuple(lista)


def _operazioni_iva(profilo: Profilo, prof: professioni.Professione) -> tuple[tuple[str, iva_estero.EsitoIva], ...]:
    casi: list[tuple[str, iva_estero.EsitoIva]] = [
        (
            "Fattura a un cliente italiano",
            iva_estero.analizza(iva_estero.Operazione(
                direzione=iva_estero.VENDITA, area=iva_estero.ITALIA,
                oggetto=iva_estero.SERVIZIO, controparte=iva_estero.B2B,
            )),
        ),
    ]
    if profilo.clienti_esteri_b2b:
        casi.append((
            "Fattura a una piattaforma o azienda UE",
            iva_estero.analizza(iva_estero.Operazione(
                direzione=iva_estero.VENDITA, area=iva_estero.UE,
                oggetto=iva_estero.SERVIZIO, controparte=iva_estero.B2B,
            )),
        ))
        casi.append((
            "Fattura a una piattaforma extra-UE",
            iva_estero.analizza(iva_estero.Operazione(
                direzione=iva_estero.VENDITA, area=iva_estero.EXTRA_UE,
                oggetto=iva_estero.SERVIZIO, controparte=iva_estero.B2B,
            )),
        ))
    if profilo.vendite_privati_ue > 0:
        casi.append((
            "Vendita a un privato di un altro Paese UE",
            iva_estero.analizza(iva_estero.Operazione(
                direzione=iva_estero.VENDITA, area=iva_estero.UE,
                oggetto=iva_estero.SERVIZIO_ELETTRONICO, controparte=iva_estero.B2C,
                vendite_ue_b2c_anno=profilo.vendite_privati_ue,
            )),
        ))
    if profilo.acquisti_servizi_esteri > 0:
        casi.append((
            "Acquisto di pubblicita' o software dall'estero",
            iva_estero.analizza(iva_estero.Operazione(
                direzione=iva_estero.ACQUISTO, area=iva_estero.UE,
                oggetto=iva_estero.SERVIZIO, controparte=iva_estero.B2B,
                importo=profilo.acquisti_servizi_esteri,
            )),
        ))
    return tuple(casi)


def analizza(profilo: Profilo, oggi: date | None = None) -> Diagnosi:
    """Produce la diagnosi completa per un profilo."""
    prof = professioni.get(profilo.professione)
    gestione = _gestione_effettiva(prof, profilo)
    verifiche = _verifiche(profilo, prof)
    bloccato = any(v.esito == BLOCCANTE for v in verifiche)

    riduzione = profilo.riduzione_richiesta
    if riduzione and gestione not in previdenza.GESTIONI_IMPRESA:
        riduzione = 0
    if riduzione == 50 and not profilo.prima_iscrizione_2025:
        riduzione = 35  # dal 2026 la riduzione al 50% non e' piu' richiedibile

    situazione = forfettario.Situazione(
        ricavi=profilo.ricavi_attesi,
        coefficiente=prof.coefficiente,
        gestione=gestione,
        startup=profilo.prima_attivita and not bloccato,
        riduzione=riduzione,
        mesi_attivita=profilo.mesi_attivita,
        gia_assicurato=profilo.gia_assicurato_altrove,
    )

    esito = forfettario.calcola(situazione)
    raffronto = confronto.confronta(situazione, profilo.costi_annui)
    piano = forfettario.piano_cassa(situazione, anni=3)

    profilo_scadenze = scadenze.Profilo(
        regime="forfettario",
        gestione=gestione,
        acquisti_esteri=profilo.acquisti_servizi_esteri > 0,
        vendite_ue_b2b=profilo.clienti_esteri_b2b,
        riduzione_contributiva_da_chiedere=gestione in previdenza.GESTIONI_IMPRESA,
        oss=profilo.vendite_privati_ue > P.SOGLIA_OSS,
    )

    avvisi: list[str] = list(prof.attenzione)
    avvisi.extend(esito.avvisi)

    if raffronto.conviene == "ordinario":
        avvisi.append(
            f"Con {profilo.costi_annui:,.0f} euro di costi reali il regime ordinario ti "
            f"lascia {abs(raffronto.differenza):,.0f} euro in piu' all'anno: il "
            "forfettario non e' la scelta automatica."
        )
    if profilo.acquisti_servizi_esteri > 0:
        avvisi.append(
            f"L'IVA sugli acquisti esteri ti costa "
            f"{iva_estero.iva_reverse_charge(profilo.acquisti_servizi_esteri):,.0f} euro "
            "l'anno che non recuperi: e' un costo tipico del digitale che il "
            "forfettario non considera."
        )
    if len(piano) > 1:
        salto = piano[1].uscite_cassa - piano[0].uscite_cassa
        if salto > 0:
            avvisi.append(
                f"Nel secondo anno le uscite passano da {piano[0].uscite_cassa:,.0f} a "
                f"{piano[1].uscite_cassa:,.0f} euro ({salto:,.0f} euro in piu'): "
                "e' l'effetto di saldo e acconti che arrivano insieme."
            )

    return Diagnosi(
        profilo=profilo,
        professione=prof,
        gestione=gestione,
        verifiche=verifiche,
        esito_forfettario=esito,
        confronto_regimi=raffronto,
        piano_cassa=piano,
        adempimenti=_adempimenti(profilo, prof, gestione),
        operazioni_iva=_operazioni_iva(profilo, prof),
        prossime_scadenze=scadenze.prossime(6, da=oggi, profilo=profilo_scadenze),
        avvisi=tuple(dict.fromkeys(avvisi)),
    )
