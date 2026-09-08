"""Motore di calcolo del regime forfettario 2026.

Rispetto ai simulatori generalisti qui si tiene conto di tre cose che nella
pratica fanno la differenza:

* i contributi si deducono per cassa (quelli *versati* nell'anno), non per
  competenza: e' la ragione per cui il primo e il secondo anno non si
  assomigliano;
* accanto al saldo esistono gli acconti, che nel secondo anno raddoppiano
  l'uscita di cassa;
* la quota da accantonare su ogni incasso non coincide con l'aliquota
  nominale del 5% o del 15%.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from . import formato
from . import parametri as P
from . import previdenza


@dataclass(frozen=True)
class Componente:
    """Una fonte di ricavo con il proprio coefficiente di redditivita'.

    Chi lavora nel digitale raramente ha una sola attivita': sponsorizzazioni
    al 78% e ricavi pubblicitari al 67% convivono nella stessa partita IVA.
    """

    etichetta: str
    ricavi: float
    coefficiente: float
    ateco: str = ""

    def __post_init__(self) -> None:
        if self.ricavi < 0:
            raise ValueError("i ricavi di una componente non possono essere negativi")
        if not 0 < self.coefficiente <= 1:
            raise ValueError("il coefficiente va espresso tra 0 e 1")

    @property
    def reddito(self) -> float:
        return round(self.ricavi * self.coefficiente, 2)


def coefficiente_medio(componenti: "tuple[Componente, ...] | list[Componente]") -> float:
    """Coefficiente unico equivalente a piu' attivita' con coefficienti diversi.

    Con piu' codici ATECO il reddito e' la somma dei ricavi di ciascuna
    attivita' moltiplicati per il proprio coefficiente (art. 1 c. 64
    L. 190/2014). La media ponderata sui ricavi produce esattamente lo stesso
    reddito, e permette di riusare senza modifiche tutto il resto del motore.
    """
    componenti = tuple(componenti)
    if not componenti:
        raise ValueError("serve almeno una componente")

    ricavi_totali = sum(c.ricavi for c in componenti)
    if ricavi_totali <= 0:
        # Nessun ricavo: il coefficiente non ha effetto, si prende il primo
        # per non restituire un valore fuori dominio.
        return componenti[0].coefficiente

    return sum(c.reddito for c in componenti) / ricavi_totali


@dataclass(frozen=True)
class Situazione:
    """Input del calcolo."""

    ricavi: float
    coefficiente: float
    gestione: str = previdenza.GESTIONE_SEPARATA
    startup: bool = False
    riduzione: int = 0
    mesi_attivita: int = 12
    gia_assicurato: bool = False
    contributi_versati: float | None = None
    """Contributi effettivamente versati nell'anno (deducibili per cassa).

    Se None si assume la situazione 'a regime': versi nell'anno l'equivalente
    di quanto maturi. E' l'ipotesi corretta dal terzo anno in poi.
    """

    def __post_init__(self) -> None:
        if self.ricavi < 0:
            raise ValueError("i ricavi non possono essere negativi")
        if not 0 < self.coefficiente <= 1:
            raise ValueError("il coefficiente va espresso tra 0 e 1")
        if not 1 <= self.mesi_attivita <= 12:
            raise ValueError("mesi_attivita deve essere compreso tra 1 e 12")

    @property
    def aliquota(self) -> float:
        return P.ALIQUOTA_SOSTITUTIVA_STARTUP if self.startup else P.ALIQUOTA_SOSTITUTIVA


@dataclass(frozen=True)
class Esito:
    """Risultato completo di un anno d'imposta in forfettario."""

    ricavi: float
    coefficiente: float
    reddito_forfetario: float
    contributi_dedotti: float
    imponibile: float
    aliquota: float
    imposta_sostitutiva: float
    contributi: previdenza.Contributi
    avvisi: tuple[str, ...] = ()
    note: tuple[str, ...] = ()

    @property
    def contributi_dovuti(self) -> float:
        return self.contributi.totale

    @property
    def totale_dovuto(self) -> float:
        return round(self.imposta_sostitutiva + self.contributi_dovuti, 2)

    @property
    def netto(self) -> float:
        return round(self.ricavi - self.totale_dovuto, 2)

    @property
    def netto_mensile(self) -> float:
        return round(self.netto / 12, 2)

    @property
    def pressione_effettiva(self) -> float:
        """Quanto pesa davvero il fisco su 100 euro fatturati."""
        if self.ricavi <= 0:
            return 0.0
        return self.totale_dovuto / self.ricavi

    @property
    def accantonamento_consigliato(self) -> float:
        """Percentuale da mettere da parte su ogni incasso, arrotondata per eccesso."""
        if self.ricavi <= 0:
            return 0.0
        grezzo = self.pressione_effettiva + 0.03  # margine per acconti e conguagli
        return min(0.60, round(grezzo * 20) / 20)  # a scatti di 5 punti


def calcola(situazione: Situazione) -> Esito:
    """Calcola imposta sostitutiva e contributi di un anno."""
    s = situazione
    reddito_forfetario = s.ricavi * s.coefficiente

    contributi = previdenza.calcola(
        reddito_forfetario,
        gestione=s.gestione,
        riduzione=s.riduzione,
        mesi_attivita=s.mesi_attivita,
        gia_assicurato=s.gia_assicurato,
    )

    dedotti = contributi.totale if s.contributi_versati is None else max(0.0, s.contributi_versati)
    # I contributi si deducono fino a capienza: l'eccedenza si porta in dichiarazione
    # come onere deducibile dal reddito complessivo, non genera imposta negativa.
    dedotti_effettivi = min(dedotti, reddito_forfetario)
    imponibile = max(0.0, reddito_forfetario - dedotti_effettivi)
    imposta = imponibile * s.aliquota

    avvisi: list[str] = []
    note: list[str] = []

    if s.ricavi > P.SOGLIA_USCITA_IMMEDIATA:
        avvisi.append(
            f"Ricavi oltre {formato.numero(P.SOGLIA_USCITA_IMMEDIATA, 0)} euro: il regime decade "
            "immediatamente, con IVA dovuta gia' su tutte le operazioni dell'anno."
        )
    elif s.ricavi > P.SOGLIA_RICAVI:
        avvisi.append(
            f"Ricavi oltre {formato.numero(P.SOGLIA_RICAVI, 0)} euro: resti in forfettario per "
            "quest'anno ma dal prossimo passi al regime ordinario."
        )
    elif s.ricavi > P.SOGLIA_RICAVI * 0.9:
        avvisi.append(
            f"Sei oltre il 90% della soglia ({formato.numero(P.SOGLIA_RICAVI, 0)} euro): valuta se "
            "spostare gli incassi di fine anno o preparare il passaggio all'ordinario."
        )

    if dedotti > reddito_forfetario:
        note.append(
            f"Contributi versati per {formato.numero(dedotti, 2)} euro superiori al reddito "
            f"forfetario: {formato.numero(dedotti - reddito_forfetario, 2)} euro restano deducibili "
            "dagli altri redditi in dichiarazione."
        )
    if s.contributi_versati is None:
        note.append(
            "Calcolo 'a regime': si assume che nell'anno tu versi quanto maturi. "
            "Nel primo anno la deduzione e' tipicamente minore, nel secondo maggiore."
        )
    if s.startup:
        note.append(
            f"Aliquota agevolata al {P.ALIQUOTA_SOSTITUTIVA_STARTUP * 100:.0f}%: vale per "
            f"{P.ANNI_ALIQUOTA_STARTUP} anni dall'apertura, se non hai svolto la stessa "
            "attivita' nei 3 anni precedenti."
        )
    if s.mesi_attivita != 12:
        note.append(
            f"Attivita' per {s.mesi_attivita} mesi: la soglia degli "
            f"{formato.numero(P.SOGLIA_RICAVI, 0)} euro va ragguagliata ad anno "
            f"({formato.numero(P.SOGLIA_RICAVI * s.mesi_attivita / 12, 0)} euro nel tuo caso)."
        )

    return Esito(
        ricavi=round(s.ricavi, 2),
        coefficiente=s.coefficiente,
        reddito_forfetario=round(reddito_forfetario, 2),
        contributi_dedotti=round(dedotti_effettivi, 2),
        imponibile=round(imponibile, 2),
        aliquota=s.aliquota,
        imposta_sostitutiva=round(imposta, 2),
        contributi=contributi,
        avvisi=tuple(avvisi),
        note=tuple(note),
    )


# ---------------------------------------------------------------------------
# ACCONTI E PIANO DI CASSA
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Acconti:
    dovuto: bool
    totale: float
    prima_rata: float
    seconda_rata: float
    nota: str


def acconti(imposta_anno: float) -> Acconti:
    """Acconti dell'anno successivo, con metodo storico (100% dell'imposta)."""
    imposta_anno = max(0.0, imposta_anno)
    if imposta_anno <= P.ACCONTO_SOGLIA_MINIMA:
        return Acconti(
            dovuto=False,
            totale=0.0,
            prima_rata=0.0,
            seconda_rata=0.0,
            nota=f"Imposta sotto {P.ACCONTO_SOGLIA_MINIMA} euro: nessun acconto dovuto.",
        )

    totale = imposta_anno * P.ACCONTO_PERCENTUALE
    if imposta_anno < P.ACCONTO_UNICA_RATA_SOTTO:
        return Acconti(
            dovuto=True,
            totale=round(totale, 2),
            prima_rata=0.0,
            seconda_rata=round(totale, 2),
            nota="Acconto in unica soluzione entro il 30 novembre.",
        )

    return Acconti(
        dovuto=True,
        totale=round(totale, 2),
        prima_rata=round(totale * P.ACCONTO_PRIMA_RATA, 2),
        seconda_rata=round(totale * P.ACCONTO_SECONDA_RATA, 2),
        nota="Prima rata (40%) entro il 30 giugno, seconda (60%) entro il 30 novembre.",
    )


@dataclass(frozen=True)
class AnnoDiCassa:
    """Un anno del piano di cassa: competenza contro esborso reale."""

    anno: int
    ricavi: float
    imposta_competenza: float
    contributi_competenza: float
    imposta_cassa: float
    contributi_cassa: float
    dettaglio: tuple[str, ...]

    @property
    def uscite_cassa(self) -> float:
        return round(self.imposta_cassa + self.contributi_cassa, 2)

    @property
    def netto_di_cassa(self) -> float:
        return round(self.ricavi - self.uscite_cassa, 2)


# Acconto contributivo: la Gestione Separata versa l'80% del contributo
# dell'anno precedente, artigiani e commercianti il 100% della quota eccedente
# il minimale. La quota fissa, invece, si paga a rate durante l'anno stesso.
ACCONTO_CONTRIBUTI_GESTIONE_SEPARATA = 0.80
ACCONTO_CONTRIBUTI_ARTIGIANI_COMMERCIANTI = 1.00


def piano_cassa(
    situazione: Situazione,
    anni: int = 3,
    crescita: float = 0.0,
    anno_iniziale: int = P.ANNO_IMPOSTA,
) -> tuple[AnnoDiCassa, ...]:
    """Simula gli esborsi reali dei primi anni di attivita'.

    Rende visibile l'effetto piu' frainteso del sistema italiano: nel primo
    anno non si versa quasi nulla, nel secondo arrivano insieme il saldo del
    primo anno e gli acconti del secondo. Chi non lo sa spende quei soldi.
    """
    if anni < 1:
        raise ValueError("servono almeno 1 anno")

    gestione_impresa = situazione.gestione in previdenza.GESTIONI_IMPRESA
    quota_acconto_contributi = (
        ACCONTO_CONTRIBUTI_ARTIGIANI_COMMERCIANTI
        if gestione_impresa
        else ACCONTO_CONTRIBUTI_GESTIONE_SEPARATA
    )

    piano: list[AnnoDiCassa] = []
    # Storico per competenza: indice 0 = anno corrente, poi si scorre.
    imposta_prec = 0.0
    acconti_versati_prec = 0.0
    variabile_prec = variabile_prec2 = 0.0
    credito_imposta = 0.0  # acconti versati in eccesso, riportati in avanti

    for indice in range(anni):
        ricavi = situazione.ricavi * ((1 + crescita) ** indice)

        # 1. I contributi di competenza dipendono solo dal reddito forfetario.
        competenza = previdenza.calcola(
            ricavi * situazione.coefficiente,
            gestione=situazione.gestione,
            riduzione=situazione.riduzione,
            mesi_attivita=situazione.mesi_attivita,
            gia_assicurato=situazione.gia_assicurato,
        )

        # 2. Contributi effettivamente versati nell'anno.
        saldo_contributi = max(0.0, variabile_prec - variabile_prec2 * quota_acconto_contributi)
        acconto_contributi = variabile_prec * quota_acconto_contributi
        contributi_cassa = saldo_contributi + acconto_contributi
        if gestione_impresa:
            # La quota fissa si versa in quattro rate nell'anno di competenza.
            contributi_cassa += competenza.quota_fissa

        # 3. L'imposta si calcola deducendo cio' che e' stato versato per cassa.
        esito = calcola(replace(situazione, ricavi=ricavi, contributi_versati=contributi_cassa))

        # 4. Imposta effettivamente versata nell'anno: saldo dell'anno prima
        # (al netto degli acconti realmente versati) piu' acconti dell'anno
        # corrente. Il credito da acconti in eccesso compensa prima il saldo e
        # poi gli acconti stessi, come avviene in F24.
        conguaglio = imposta_prec - acconti_versati_prec - credito_imposta
        saldo_imposta = max(0.0, conguaglio)
        credito_imposta = max(0.0, -conguaglio)

        acconto_dovuto = acconti(imposta_prec).totale
        compensazione = min(credito_imposta, acconto_dovuto)
        acconto_imposta = acconto_dovuto - compensazione
        credito_imposta -= compensazione

        imposta_cassa = saldo_imposta + acconto_imposta

        dettaglio: list[str] = []
        if indice == 0:
            dettaglio.append("Primo anno: nessun saldo e nessun acconto d'imposta da versare.")
        else:
            dettaglio.append(f"Saldo imposta anno precedente: {formato.numero(saldo_imposta, 2)} euro.")
            dettaglio.append(f"Acconti imposta dell'anno: {formato.numero(acconto_imposta, 2)} euro.")
            if compensazione:
                dettaglio.append(
                    f"Credito da acconti in eccesso usato in compensazione: "
                    f"{formato.numero(compensazione, 2)} euro."
                )
        if gestione_impresa:
            dettaglio.append(
                f"Quota fissa INPS in quattro rate: {formato.numero(competenza.quota_fissa, 2)} euro."
            )
        if contributi_cassa - (competenza.quota_fissa if gestione_impresa else 0.0) > 0:
            dettaglio.append(
                f"Saldo e acconti contributivi: "
                f"{formato.numero(contributi_cassa - (competenza.quota_fissa if gestione_impresa else 0.0), 2)} euro."
            )
        elif indice == 0 and not gestione_impresa:
            dettaglio.append(
                "Nessun contributo versato: in Gestione Separata il primo versamento "
                "cade a giugno dell'anno successivo."
            )

        piano.append(
            AnnoDiCassa(
                anno=anno_iniziale + indice,
                ricavi=round(ricavi, 2),
                imposta_competenza=esito.imposta_sostitutiva,
                contributi_competenza=competenza.totale,
                imposta_cassa=round(imposta_cassa, 2),
                contributi_cassa=round(contributi_cassa, 2),
                dettaglio=tuple(dettaglio),
            )
        )

        imposta_prec = esito.imposta_sostitutiva
        acconti_versati_prec = acconto_imposta
        variabile_prec2, variabile_prec = variabile_prec, competenza.quota_variabile

    return tuple(piano)


def ricavi_per_netto_obiettivo(
    netto_obiettivo: float,
    situazione: Situazione,
    tolleranza: float = 1.0,
) -> float:
    """Quanto devo fatturare per portare a casa X euro netti?

    Domanda che ogni freelance si fa e che nessun simulatore risolve al
    contrario. Risolta per bisezione: la funzione e' monotona crescente.
    """
    if netto_obiettivo <= 0:
        return 0.0

    basso, alto = 0.0, max(netto_obiettivo * 4, 10_000.0)
    for _ in range(200):
        medio = (basso + alto) / 2
        netto = calcola(replace(situazione, ricavi=medio)).netto
        if abs(netto - netto_obiettivo) <= tolleranza:
            return round(medio, 2)
        if netto < netto_obiettivo:
            basso = medio
        else:
            alto = medio
    return round((basso + alto) / 2, 2)
