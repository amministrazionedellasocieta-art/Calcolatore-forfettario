"""Regime ordinario (contabilita' semplificata) per persone fisiche.

Serve come termine di paragone: il forfettario non conviene sempre, e per
alcuni lavori digitali (dropshipping, e-commerce, chi compra molta
pubblicita') conviene quasi mai.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import formato
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
    reddito_complessivo: float
    contributi: previdenza.Contributi
    imponibile_irpef: float
    irpef_lorda: float
    detrazione: float
    irpef: float
    addizionali: float
    scaglioni: tuple[tuple[float, float, float], ...]
    note: tuple[str, ...] = ()

    @property
    def contributi_dovuti(self) -> float:
        return self.contributi.totale

    @property
    def imposte(self) -> float:
        """IRPEF netta (dopo la detrazione, mai negativa) piu' addizionali."""
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


def detrazione_lavoro_autonomo(reddito_complessivo: float) -> float:
    """Detrazione dell'art. 13 c. 5 TUIR, parametrata al reddito complessivo.

    Non e' un dettaglio trascurabile nel confronto tra regimi: sotto i 50.000
    euro vale fino a 1.265 euro di imposta in meno, e ignorarla fa sembrare
    l'ordinario piu' caro di quanto sia.
    """
    reddito = max(0.0, reddito_complessivo)

    if reddito <= P.DETRAZIONE_AUTONOMI_SOGLIA_PIENA:
        return P.DETRAZIONE_AUTONOMI_MASSIMA

    if reddito <= P.DETRAZIONE_AUTONOMI_SOGLIA_INTERMEDIA:
        residuo = P.DETRAZIONE_AUTONOMI_SOGLIA_INTERMEDIA - reddito
        ampiezza = P.DETRAZIONE_AUTONOMI_SOGLIA_INTERMEDIA - P.DETRAZIONE_AUTONOMI_SOGLIA_PIENA
        return round(
            P.DETRAZIONE_AUTONOMI_BASE_INTERMEDIA
            + P.DETRAZIONE_AUTONOMI_QUOTA_DECRESCENTE * residuo / ampiezza,
            2,
        )

    if reddito <= P.DETRAZIONE_AUTONOMI_SOGLIA_AZZERAMENTO:
        residuo = P.DETRAZIONE_AUTONOMI_SOGLIA_AZZERAMENTO - reddito
        ampiezza = (
            P.DETRAZIONE_AUTONOMI_SOGLIA_AZZERAMENTO - P.DETRAZIONE_AUTONOMI_SOGLIA_INTERMEDIA
        )
        return round(P.DETRAZIONE_AUTONOMI_BASE_INTERMEDIA * residuo / ampiezza, 2)

    return 0.0


def reddito_diritti_autore(compenso: float, eta: int | None = None) -> float:
    """Imponibile dei diritti d'autore percepiti dall'autore stesso.

    Non e' reddito forfettario ne' d'impresa: e' lavoro autonomo con
    abbattimento forfetario delle spese (art. 53 c. 2 lett. b TUIR), piu'
    generoso per gli under 35. Riguarda musicisti, autori self-publishing,
    fotografi e illustratori del catalogo.
    """
    compenso = max(0.0, compenso)
    abbattimento = (
        P.ABBATTIMENTO_DIRITTO_AUTORE_UNDER35
        if eta is not None and eta < P.ETA_ABBATTIMENTO_MAGGIORE
        else P.SOGLIA_DIRITTO_AUTORE_ABBATTIMENTO
    )
    return round(compenso * (1 - abbattimento), 2)


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

    reddito_complessivo = reddito + s.altri_redditi
    # I contributi obbligatori sono oneri deducibili dal reddito complessivo.
    imponibile = max(0.0, reddito_complessivo - contributi.totale)
    imposta_lorda, dettaglio = irpef(imponibile)

    # La detrazione e' parametrata al reddito complessivo, non all'imponibile,
    # e non genera credito: al massimo azzera l'imposta.
    detrazione = detrazione_lavoro_autonomo(reddito_complessivo)
    detrazione_effettiva = min(detrazione, imposta_lorda)
    imposta_netta = imposta_lorda - detrazione_effettiva

    # Le addizionali non sono dovute quando l'IRPEF netta e' azzerata dalle
    # detrazioni (art. 1 c. 4 D.Lgs. 360/1998 per la comunale, analogamente
    # per la regionale).
    addizionali = (
        imponibile * (s.addizionale_regionale + s.addizionale_comunale)
        if imposta_netta > 0
        else 0.0
    )

    note = [
        f"Detrazione per redditi di lavoro autonomo applicata: "
        f"{formato.numero(detrazione_effettiva, 2)} euro (art. 13 c. 5 TUIR).",
        "Non sono incluse detrazioni personali, familiari a carico e oneri "
        "detraibili, che riducono ulteriormente il dovuto.",
        "L'IVA non e' un costo: la incassi dal cliente e la riversi allo Stato, "
        "ma detrai quella sugli acquisti (cosa impossibile nel forfettario).",
    ]
    if reddito > 0 and s.gestione == previdenza.GESTIONE_SEPARATA:
        note.append(
            "Con la Gestione Separata puoi addebitare in fattura la rivalsa del "
            "4%, che aumenta il compenso concordato."
        )

    if detrazione > detrazione_effettiva:
        note.append(
            f"Detrazione non utilizzata per incapienza: {formato.numero(detrazione - detrazione_effettiva, 2)} "
            "euro non recuperabili, perche' la detrazione non genera credito."
        )
    if imposta_netta <= 0 and imponibile > 0:
        note.append("IRPEF azzerata dalla detrazione: le addizionali non sono dovute.")

    return EsitoOrdinario(
        ricavi=round(s.ricavi, 2),
        costi=round(s.costi, 2),
        reddito=round(reddito, 2),
        reddito_complessivo=round(reddito_complessivo, 2),
        contributi=contributi,
        imponibile_irpef=round(imponibile, 2),
        irpef_lorda=imposta_lorda,
        detrazione=round(detrazione_effettiva, 2),
        irpef=round(imposta_netta, 2),
        addizionali=round(addizionali, 2),
        scaglioni=dettaglio,
        note=tuple(note),
    )
