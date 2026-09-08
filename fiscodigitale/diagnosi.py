"""Diagnosi fiscale completa a partire dal lavoro reale.

E' il modulo che tiene insieme gli altri: si parte da "faccio lo streamer e
prevedo 40.000 euro", si arriva a inquadramento, verifica dei requisiti,
numeri, adempimenti e scadenze. Il ragionamento che un commercialista fa alla
prima consulenza, reso ripetibile.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date

from . import formato
from . import confronto, forfettario, iva_estero
from . import parametri as P
from . import previdenza, professioni, scadenze

OK = "ok"
ATTENZIONE = "attenzione"
BLOCCANTE = "bloccante"

# Natura dell'attivita': non dipende dal fatturato ma da come si lavora.
PROFESSIONALE = "professionale"
IMPRESA = "impresa"


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


def _verifica_slug(slug: str) -> None:
    """Fallisce subito, con un messaggio leggibile, se la professione non esiste."""
    if slug not in professioni.slugs():
        raise ValueError(
            f"professione sconosciuta: {slug!r}. "
            "Usa uno degli slug del catalogo (fiscodigitale --elenco)."
        )


@dataclass(frozen=True)
class AltraAttivita:
    """Una fonte di ricavo ulteriore rispetto all'attivita' principale."""

    professione: str
    ricavi: float
    natura_attivita: str | None = None

    def __post_init__(self) -> None:
        if self.ricavi < 0:
            raise ValueError("i ricavi di un'attivita' non possono essere negativi")
        if self.natura_attivita not in (None, PROFESSIONALE, IMPRESA):
            raise ValueError(f"natura_attivita non valida: {self.natura_attivita!r}")
        _verifica_slug(self.professione)


@dataclass(frozen=True)
class AttivitaRisolta:
    """Un'attivita' con il suo inquadramento gia' determinato."""

    professione: professioni.Professione
    ricavi: float
    gestione: str
    scelta_pendente: bool
    componente: forfettario.Componente

    @property
    def reddito(self) -> float:
        return self.componente.reddito

    @property
    def e_impresa(self) -> bool:
        return self.gestione in previdenza.GESTIONI_IMPRESA


@dataclass(frozen=True)
class Profilo:
    """Come lavori davvero."""

    professione: str
    ricavi_attesi: float
    costi_annui: float = 0.0
    prima_attivita: bool = True
    mesi_attivita: int = 12
    gestione_scelta: str | None = None
    altre_attivita: tuple[AltraAttivita, ...] = ()
    """Altre fonti di ricavo con codice ATECO diverso da quello principale.

    Con piu' attivita' il limite degli 85.000 euro si misura sulla somma dei
    ricavi, ma il coefficiente si applica a ciascuna separatamente.
    """
    natura_attivita: str | None = None
    """Come eserciti: "professionale" o "impresa".

    Per molti lavori digitali il mestiere da solo non lo determina. Lasciarlo a
    None non e' un errore: la diagnosi lo segnala come scelta da compiere
    invece di indovinarla.
    """
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
        _verifica_slug(self.professione)
        if self.natura_attivita not in (None, PROFESSIONALE, IMPRESA):
            raise ValueError(
                f"natura_attivita non valida: {self.natura_attivita!r}"
            )
        slugs = [self.professione] + [a.professione for a in self.altre_attivita]
        if len(slugs) != len(set(slugs)):
            raise ValueError(
                "la stessa professione compare piu' volte: somma i ricavi in una sola voce"
            )

    @property
    def ricavi_totali(self) -> float:
        return round(self.ricavi_attesi + sum(a.ricavi for a in self.altre_attivita), 2)

    @property
    def multi_attivita(self) -> bool:
        return bool(self.altre_attivita)


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
    inquadramento_da_scegliere: bool = False
    costo_inquadramento: dict[str, float] | None = None
    attivita: tuple[AttivitaRisolta, ...] = ()
    coefficiente_medio: float = 0.0
    contributi_doppia_iscrizione: float | None = None

    @property
    def multi_attivita(self) -> bool:
        return len(self.attivita) > 1

    @property
    def ricavi_totali(self) -> float:
        return self.profilo.ricavi_totali

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
        if self.multi_attivita:
            codici = ", ".join(
                f"{a.professione.ateco or 'senza codice'} al {a.professione.coefficiente_pct}%"
                for a in self.attivita
            )
            intestazione = (
                f"{len(self.attivita)} attivita' ({codici}), coefficiente medio "
                f"{self.coefficiente_medio * 100:.1f}%, {previdenza_label(self.gestione)}."
            )
        else:
            intestazione = (
                f"{self.professione.nome} - ATECO {self.professione.ateco}, coefficiente "
                f"{self.professione.coefficiente_pct}%, {previdenza_label(self.gestione)}."
            )
        return (
            f"{intestazione} "
            f"Su {formato.numero(self.ricavi_totali, 0)} euro di ricavi versi "
            f"{formato.numero(self.esito_forfettario.totale_dovuto, 0)} euro tra imposta e contributi "
            f"({self.esito_forfettario.pressione_effettiva * 100:.1f}%) e ne restano "
            f"{formato.numero(self.netto_reale, 0)} netti."
        )


def previdenza_label(gestione: str) -> str:
    return professioni.LABEL_GESTIONE.get(gestione, gestione)


def _gestione_effettiva(
    prof: professioni.Professione,
    natura_attivita: str | None = None,
    gestione_scelta: str | None = None,
) -> tuple[str, bool]:
    """Cassa previdenziale applicabile e se resta una scelta da compiere.

    Per le professioni il cui inquadramento dipende dall'organizzazione
    concreta non si indovina in base al fatturato: si assume la forma
    professionale, meno onerosa, e si segnala la scelta all'utente.
    """
    if gestione_scelta:
        return gestione_scelta, False

    mappa = {
        professioni.GS: previdenza.GESTIONE_SEPARATA,
        professioni.COMMERCIANTI: previdenza.COMMERCIANTI,
        professioni.ARTIGIANI: previdenza.ARTIGIANI,
        professioni.NESSUNO: previdenza.NESSUNA,
    }
    if prof.gestione_inps != professioni.DIPENDE:
        return mappa[prof.gestione_inps], False

    if natura_attivita == IMPRESA:
        gestione = previdenza.COMMERCIANTI if prof.camera_commercio else previdenza.ARTIGIANI
        return gestione, False
    if natura_attivita == PROFESSIONALE:
        return previdenza.GESTIONE_SEPARATA, False

    return previdenza.GESTIONE_SEPARATA, True


def _risolvi_attivita(profilo: Profilo) -> tuple[AttivitaRisolta, ...]:
    """Determina inquadramento e componente di reddito per ogni attivita'."""
    voci: list[tuple[str, float, str | None]] = [
        (profilo.professione, profilo.ricavi_attesi, profilo.natura_attivita)
    ]
    voci.extend((a.professione, a.ricavi, a.natura_attivita) for a in profilo.altre_attivita)

    risolte: list[AttivitaRisolta] = []
    for slug, ricavi, natura in voci:
        prof = professioni.get(slug)
        gestione, pendente = _gestione_effettiva(prof, natura, profilo.gestione_scelta)
        risolte.append(AttivitaRisolta(
            professione=prof,
            ricavi=round(ricavi, 2),
            gestione=gestione,
            scelta_pendente=pendente,
            componente=forfettario.Componente(
                etichetta=prof.nome,
                ricavi=ricavi,
                coefficiente=prof.coefficiente,
                ateco=prof.ateco,
            ),
        ))
    return tuple(risolte)


def _contributi_doppia_iscrizione(
    attivita: tuple[AttivitaRisolta, ...], profilo: Profilo, riduzione: int
) -> float:
    """Contributi se INPS richiede l'iscrizione a entrambe le gestioni."""
    reddito_professionale = sum(a.reddito for a in attivita if not a.e_impresa)
    reddito_impresa = sum(a.reddito for a in attivita if a.e_impresa)
    gestione_impresa = next(a.gestione for a in attivita if a.e_impresa)

    totale = previdenza.gestione_separata(
        reddito_professionale, gia_assicurato=profilo.gia_assicurato_altrove
    ).totale
    totale += previdenza.artigiani_commercianti(
        reddito_impresa,
        gestione=gestione_impresa,
        riduzione=riduzione,
        mesi_attivita=profilo.mesi_attivita,
    ).totale
    return round(totale, 2)


def _costo_inquadramento(
    prof: professioni.Professione, profilo: Profilo, riduzione: int, reddito: float
) -> dict[str, float]:
    """Quanto costa, in contributi, l'una o l'altra forma di esercizio."""
    gestione_impresa = previdenza.COMMERCIANTI if prof.camera_commercio else previdenza.ARTIGIANI

    come_professionista = previdenza.calcola(
        reddito,
        gestione=previdenza.GESTIONE_SEPARATA,
        mesi_attivita=profilo.mesi_attivita,
        gia_assicurato=profilo.gia_assicurato_altrove,
    ).totale
    come_impresa = previdenza.calcola(
        reddito,
        gestione=gestione_impresa,
        riduzione=riduzione,
        mesi_attivita=profilo.mesi_attivita,
    ).totale

    return {
        "professionale": round(come_professionista, 2),
        "impresa": round(come_impresa, 2),
        "differenza": round(come_impresa - come_professionista, 2),
    }


def _verifiche(profilo: Profilo, prof: professioni.Professione) -> tuple[Verifica, ...]:
    v: list[Verifica] = []
    soglia_ragguagliata = P.SOGLIA_RICAVI * profilo.mesi_attivita / 12
    # Con piu' codici ATECO il limite si misura sulla somma dei ricavi di
    # tutte le attivita' (art. 1 c. 54 L. 190/2014).
    ricavi = profilo.ricavi_totali

    if ricavi > P.SOGLIA_USCITA_IMMEDIATA:
        v.append(Verifica(
            "Limite dei ricavi", BLOCCANTE,
            f"Ricavi previsti di {formato.numero(ricavi, 0)} euro: oltre "
            f"{formato.numero(P.SOGLIA_USCITA_IMMEDIATA, 0)} euro il regime decade nell'anno stesso.",
            "art. 1 c. 71 L. 190/2014",
        ))
    elif ricavi > soglia_ragguagliata:
        v.append(Verifica(
            "Limite dei ricavi", ATTENZIONE,
            f"Ricavi previsti di {formato.numero(ricavi, 0)} euro contro un limite di "
            f"{formato.numero(soglia_ragguagliata, 0)}: userai il forfettario quest'anno e passerai "
            "all'ordinario dal prossimo.",
            "art. 1 c. 54 L. 190/2014",
        ))
    else:
        v.append(Verifica(
            "Limite dei ricavi", OK,
            f"{formato.numero(ricavi, 0)} euro su un limite di {formato.numero(soglia_ragguagliata, 0)}: "
            f"hai ancora {formato.numero(soglia_ragguagliata - ricavi, 0)} euro di margine.",
        ))

    if 0 < ricavi <= P.SOGLIA_PRESTAZIONE_OCCASIONALE_INPS:
        v.append(Verifica(
            "Serve davvero la partita IVA?", ATTENZIONE,
            f"Con {formato.euro(ricavi)} di ricavi previsti valuta prima se l'attivita' "
            "e' occasionale: in quel caso basta la ricevuta per prestazione occasionale, "
            f"e sotto {formato.euro(P.SOGLIA_PRESTAZIONE_OCCASIONALE_INPS)} l'anno non e' "
            "dovuta nemmeno l'iscrizione alla Gestione Separata. Attenzione pero': la "
            "soglia riguarda i contributi, non l'obbligo di partita IVA, che dipende "
            "dall'abitualita' dell'attivita' e non dall'importo.",
            "art. 44 c. 2 DL 269/2003; art. 5 DPR 633/72",
        ))

    if profilo.redditi_dipendente_anno_precedente > P.SOGLIA_REDDITI_DIPENDENTE:
        v.append(Verifica(
            "Redditi da lavoro dipendente", BLOCCANTE,
            f"Nell'anno precedente hai percepito "
            f"{formato.numero(profilo.redditi_dipendente_anno_precedente, 0)} euro da lavoro dipendente "
            f"o pensione, oltre il limite di {formato.numero(P.SOGLIA_REDDITI_DIPENDENTE, 0)}. "
            "Il limite non opera se il rapporto di lavoro e' cessato.",
            "art. 1 c. 57 lett. d-ter L. 190/2014",
        ))
    elif profilo.redditi_dipendente_anno_precedente > 0:
        v.append(Verifica(
            "Redditi da lavoro dipendente", OK,
            f"{formato.numero(profilo.redditi_dipendente_anno_precedente, 0)} euro sotto il limite di "
            f"{formato.numero(P.SOGLIA_REDDITI_DIPENDENTE, 0)} euro: puoi cumulare lavoro dipendente e "
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
            f"{formato.numero(profilo.spese_personale, 0)} euro di costi per dipendenti e "
            f"collaboratori, oltre il limite di {formato.numero(P.LIMITE_SPESE_PERSONALE, 0)}.",
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
            f"(circa {formato.numero(P.COMMERCIANTI['contributo_fisso'], 0)} euro l'anno). "
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
            f"Su {formato.numero(profilo.acquisti_servizi_esteri, 0)} euro di servizi esteri (pubblicita', "
            f"software, commissioni) devi integrare le fatture e versare "
            f"{formato.numero(iva_annua, 0)} euro di IVA che nel forfettario non recuperi.",
            f"TD17 entro il {P.GIORNO_AUTOFATTURA_ACQUISTI} e F24 entro il "
            f"{P.GIORNO_VERSAMENTO_IVA_REVERSE} del mese successivo",
            costo_indicativo=f"{formato.numero(iva_annua, 0)} euro l'anno di IVA indetraibile",
        ))

    if profilo.vendite_privati_ue > P.SOGLIA_OSS:
        lista.append(Adempimento(
            "Valutazione del regime OSS",
            f"Le vendite a privati UE ({formato.numero(profilo.vendite_privati_ue, 0)} euro) superano "
            f"la soglia di {formato.numero(P.SOGLIA_OSS, 0)} euro: si applica l'IVA del Paese del "
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
    attivita = _risolvi_attivita(profilo)

    # L'inquadramento previdenziale segue l'attivita' prevalente per ricavi,
    # non quella dichiarata per prima.
    prevalente = max(attivita, key=lambda a: a.ricavi)
    gestione = prevalente.gestione

    # Basta una sola attivita' senza natura dichiarata perche' la diagnosi
    # resti aperta: anche una secondaria puo' richiedere il trattamento
    # d'impresa e una posizione contributiva a se'.
    attive = tuple(a for a in attivita if a.ricavi > 0) or attivita
    da_chiarire = tuple(a for a in attive if a.scelta_pendente)
    scelta_pendente = bool(da_chiarire)

    coefficiente = forfettario.coefficiente_medio([a.componente for a in attivita])
    verifiche = list(_verifiche(profilo, prof))
    bloccato = any(v.esito == BLOCCANTE for v in verifiche)

    riduzione = profilo.riduzione_richiesta
    if riduzione and gestione not in previdenza.GESTIONI_IMPRESA:
        riduzione = 0
    if riduzione == 50 and not profilo.prima_iscrizione_2025:
        riduzione = 35  # dal 2026 la riduzione al 50% non e' piu' richiedibile

    situazione = forfettario.Situazione(
        ricavi=profilo.ricavi_totali,
        coefficiente=coefficiente,
        gestione=gestione,
        startup=profilo.prima_attivita and not bloccato,
        riduzione=riduzione,
        mesi_attivita=profilo.mesi_attivita,
        gia_assicurato=profilo.gia_assicurato_altrove,
    )

    esito = forfettario.calcola(situazione)
    raffronto = confronto.confronta(situazione, profilo.costi_annui)
    piano = forfettario.piano_cassa(situazione, anni=3)

    costo_inquadramento = None
    if da_chiarire or prevalente.professione.gestione_inps == professioni.DIPENDE:
        # Il confronto riguarda l'attivita' da chiarire piu' rilevante, che non
        # coincide necessariamente con la prevalente.
        oggetto = max(da_chiarire, key=lambda a: a.ricavi) if da_chiarire else prevalente
        costo_inquadramento = _costo_inquadramento(
            oggetto.professione, profilo, riduzione, oggetto.reddito
        )
        if scelta_pendente:
            delta = costo_inquadramento["differenza"]
            if abs(delta) < 1:
                verso = "Con i tuoi numeri le due forme costano quasi uguale"
            elif delta > 0:
                verso = (
                    f"Con i tuoi numeri la forma d'impresa costa "
                    f"{formato.numero(delta, 0)} euro in piu'"
                )
            else:
                verso = (
                    f"Con i tuoi numeri la forma d'impresa costa "
                    f"{formato.numero(abs(delta), 0)} euro in meno"
                )
            quale = (
                f"L'attivita' da chiarire e' {oggetto.professione.nome}. "
                if len(attivita) > 1
                else ""
            )
            verifiche.append(Verifica(
                "Inquadramento da confermare",
                ATTENZIONE,
                f"{quale}Questo lavoro puo' essere esercitato in forma professionale o "
                "d'impresa, e non lo decide il fatturato: dipende da quanto pesano "
                "l'organizzazione e i mezzi rispetto al tuo apporto personale. "
                f"{verso}: {formato.numero(costo_inquadramento['professionale'], 0)} euro in "
                f"Gestione Separata contro {formato.numero(costo_inquadramento['impresa'], 0)} "
                "come impresa. Attenzione pero' al profilo di rischio: la quota fissa "
                "dell'impresa e' dovuta anche in un anno senza incassi, la Gestione "
                "Separata no. Il calcolo assume la forma professionale: indica come "
                "lavori per avere i numeri giusti.",
                "art. 2195 c.c.; art. 53 TUIR",
            ))

    if not prof.ateco:
        aliquota = P.CRIPTO["aliquota_plusvalenze"]
        verifiche.append(Verifica(
            "Non e' un'attivita' con partita IVA", ATTENZIONE,
            "Chi investe in proprio non esercita un'attivita' d'impresa: le "
            f"plusvalenze sono redditi diversi tassati al "
            f"{formato.percentuale(aliquota, 0)} con imposta sostitutiva, piu' "
            f"l'imposta sul valore delle cripto-attivita' del "
            f"{P.CRIPTO['imposta_valore_cripto'] * 1000:.0f} per mille. I numeri del "
            "forfettario qui sotto non ti riguardano: usa il modulo dedicato alle "
            "cripto-attivita'.",
            P.FONTI["cripto"],
        ))

    contributi_doppia = None
    if profilo.multi_attivita:
        attive = tuple(a for a in attivita if a.ricavi > 0)
        if prevalente.professione.slug != prof.slug:
            verifiche.append(Verifica(
                "Attivita' prevalente",
                ATTENZIONE,
                f"L'attivita' con piu' ricavi non e' quella che hai indicato come "
                f"principale ma {prevalente.professione.nome} "
                f"({formato.numero(prevalente.ricavi, 0)} euro). L'inquadramento previdenziale segue "
                "la prevalente: verifica quale codice ATECO hai dichiarato come primario.",
                "art. 1 c. 54 L. 190/2014",
            ))

        nature = {a.e_impresa for a in attive}
        if len(nature) > 1:
            contributi_doppia = _contributi_doppia_iscrizione(attive, profilo, riduzione)
            differenza = contributi_doppia - esito.contributi_dovuti
            verifiche.append(Verifica(
                "Attivita' di natura diversa",
                ATTENZIONE,
                "Stai cumulando un'attivita' professionale e una d'impresa. INPS puo' "
                "richiedere l'iscrizione a entrambe le gestioni, ciascuna sul proprio "
                f"reddito: in quel caso i contributi salgono a {formato.numero(contributi_doppia, 0)} "
                f"euro ({differenza:+,.0f} rispetto ai {formato.numero(esito.contributi_dovuti, 0)} "
                "calcolati sulla sola gestione prevalente). E' una situazione da "
                "impostare con un professionista prima di aprire la posizione.",
                "art. 1 c. 208 L. 662/1996",
            ))

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
            f"Con {formato.numero(profilo.costi_annui, 0)} euro di costi reali il regime ordinario ti "
            f"lascia {formato.numero(abs(raffronto.differenza), 0)} euro in piu' all'anno: il "
            "forfettario non e' la scelta automatica."
        )
    if profilo.acquisti_servizi_esteri > 0:
        avvisi.append(
            f"L'IVA sugli acquisti esteri ti costa "
            f"{formato.numero(iva_estero.iva_reverse_charge(profilo.acquisti_servizi_esteri), 0)} euro "
            "l'anno che non recuperi: e' un costo tipico del digitale che il "
            "forfettario non considera."
        )
    if len(piano) > 1:
        salto = piano[1].uscite_cassa - piano[0].uscite_cassa
        if salto > 0:
            avvisi.append(
                f"Nel secondo anno le uscite passano da {formato.numero(piano[0].uscite_cassa, 0)} a "
                f"{formato.numero(piano[1].uscite_cassa, 0)} euro ({formato.numero(salto, 0)} euro in piu'): "
                "e' l'effetto di saldo e acconti che arrivano insieme."
            )

    return Diagnosi(
        profilo=profilo,
        professione=prof,
        gestione=gestione,
        verifiche=tuple(verifiche),
        esito_forfettario=esito,
        confronto_regimi=raffronto,
        piano_cassa=piano,
        adempimenti=_adempimenti(profilo, prof, gestione),
        operazioni_iva=_operazioni_iva(profilo, prof),
        prossime_scadenze=scadenze.prossime(6, da=oggi, profilo=profilo_scadenze),
        avvisi=tuple(dict.fromkeys(avvisi)),
        inquadramento_da_scegliere=scelta_pendente,
        costo_inquadramento=costo_inquadramento,
        attivita=attivita,
        coefficiente_medio=round(coefficiente, 6),
        contributi_doppia_iscrizione=contributi_doppia,
    )
