"""Regime ordinario (contabilita' semplificata) per persone fisiche.

Serve come termine di paragone: il forfettario non conviene sempre, e per
alcuni lavori digitali (dropshipping, e-commerce, chi compra molta
pubblicita') conviene quasi mai.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import parametri as P
from . import previdenza


@dataclass(frozen=True)
class SituazioneOrdinario:
    ricavi: float
    costi: float = 0.0
    gestione: str = previdenza.GESTIONE_SEPARATA
    mesi_attivita: int = 12
    gia_assicurato: bool = False
    addizionale_regionale: float = P.ADDIZIONALE_REGIONALE_MEDIA
    addizionale_comunale: float = P.ADDIZIONALE_COMUNALE_MEDIA
    altri_redditi: float = 0.0

    def __post_init__(self) -> None:
        if self.ricavi < 0 or self.costi < 0:
            raise ValueError("ricavi e costi non possono essere negativi")


@dataclass(frozen=True)
class EsitoOrdinario:
    ricavi: float
    costi: float
    reddito: float
    contributi: previdenza.Contributi
    imponibile_irpef: float
    irpef: float
    addizionali: float
    scaglioni: tuple[tuple[float, float, float], ...]
    note: tuple[str, ...] = ()

    @property
    def contributi_dovuti(self) -> float:
        return self.contributi.totale

    @property
    def imposte(self) -> float:
        return round(self.irpef + self.addizionali, 2)

    @property
    def totale_dovuto(self) -> float:
        return round(self.imposte + self.contributi_dovuti, 2)

    @property
    def netto(self) -> float:
        """Netto in tasca: ricavi meno costi reali, imposte e contributi."""
        return round(self.ricavi - self.costi - self.totale_dovuto, 2)

    @property
    def pressione_effettiva(self) -> float:
        if self.ricavi <= 0:
            return 0.0
        return self.totale_dovuto / self.ricavi

    @property
    def aliquota_marginale(self) -> float:
        return aliquota_marginale(self.imponibile_irpef)


def irpef(imponibile: float) -> tuple[float, tuple[tuple[float, float, float], ...]]:
    """IRPEF lorda e dettaglio per scaglione: (base, aliquota, imposta)."""
    imponibile = max(0.0, imponibile)
    imposta = 0.0
    dettaglio: list[tuple[float, float, float]] = []
    limite_precedente = 0.0

    for limite, aliquota in P.SCAGLIONI_IRPEF:
        base = max(0.0, min(imponibile, limite) - limite_precedente)
        if base > 0:
            quota = base * aliquota
            imposta += quota
            dettaglio.append((round(base, 2), aliquota, round(quota, 2)))
        limite_precedente = limite
        if imponibile <= limite:
            break

    return round(imposta, 2), tuple(dettaglio)


def aliquota_marginale(imponibile: float) -> float:
    for limite, aliquota in P.SCAGLIONI_IRPEF:
        if imponibile <= limite:
            return aliquota
    return P.SCAGLIONI_IRPEF[-1][1]


def calcola(situazione: SituazioneOrdinario) -> EsitoOrdinario:
    s = situazione
    reddito = max(0.0, s.ricavi - s.costi)

    contributi = previdenza.calcola(
        reddito,
        gestione=s.gestione,
        riduzione=0,  # le riduzioni per forfettari non si applicano nell'ordinario
        mesi_attivita=s.mesi_attivita,
        gia_assicurato=s.gia_assicurato,
    )

    # I contributi obbligatori sono oneri deducibili dal reddito complessivo.
    imponibile = max(0.0, reddito + s.altri_redditi - contributi.totale)
    imposta_lorda, dettaglio = irpef(imponibile)
    addizionali = imponibile * (s.addizionale_regionale + s.addizionale_comunale)

    note = [
        "Calcolo semplificato: non include detrazioni personali, familiari a "
        "carico, oneri detraibili e crediti d'imposta, che riducono il dovuto.",
        "L'IVA non e' un costo: la incassi dal cliente e la riversi allo Stato, "
        "ma detrai quella sugli acquisti (cosa impossibile nel forfettario).",
    ]
    if reddito > 0 and s.gestione == previdenza.GESTIONE_SEPARATA:
        note.append(
            "Con la Gestione Separata puoi addebitare in fattura la rivalsa del "
            "4%, che aumenta il compenso concordato."
        )

    return EsitoOrdinario(
        ricavi=round(s.ricavi, 2),
        costi=round(s.costi, 2),
        reddito=round(reddito, 2),
        contributi=contributi,
        imponibile_irpef=round(imponibile, 2),
        irpef=imposta_lorda,
        addizionali=round(addizionali, 2),
        scaglioni=dettaglio,
        note=tuple(note),
    )
