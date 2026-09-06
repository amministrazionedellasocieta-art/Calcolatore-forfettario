"""Calcolo dei contributi previdenziali 2026.

Copre le due gestioni che riguardano quasi tutto il lavoro digitale:
Gestione Separata (professionisti) e Gestione Artigiani/Commercianti
(chi esercita in forma d'impresa: e-commerce, influencer strutturati, ...).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import parametri as P

GESTIONE_SEPARATA = "gestione_separata"
ARTIGIANI = "artigiani"
COMMERCIANTI = "commercianti"
NESSUNA = "nessuna"

GESTIONI_IMPRESA = (ARTIGIANI, COMMERCIANTI)


@dataclass(frozen=True)
class Contributi:
    """Esito del calcolo contributivo di un anno."""

    gestione: str
    imponibile: float
    quota_fissa: float = 0.0
    quota_variabile: float = 0.0
    riduzione_applicata: int = 0
    risparmio_riduzione: float = 0.0
    note: tuple[str, ...] = ()

    @property
    def totale(self) -> float:
        return self.quota_fissa + self.quota_variabile

    @property
    def aliquota_effettiva(self) -> float:
        if self.imponibile <= 0:
            return 0.0
        return self.totale / self.imponibile


def _arrotonda(valore: float) -> float:
    return round(valore + 1e-9, 2)


def gestione_separata(
    imponibile: float,
    *,
    gia_assicurato: bool = False,
) -> Contributi:
    """Contributi Gestione Separata per professionisti con partita IVA.

    Non esiste un contributo minimo: si paga in percentuale sul reddito
    effettivo. Il minimale rileva solo per l'accredito dei mesi di anzianita'.
    """
    imponibile = max(0.0, imponibile)
    imponibile_tassabile = min(imponibile, P.GESTIONE_SEPARATA["massimale"])
    aliquota = (
        P.GESTIONE_SEPARATA["aliquota_gia_assicurati"]
        if gia_assicurato
        else P.GESTIONE_SEPARATA["aliquota_professionisti"]
    )

    note: list[str] = [
        f"Aliquota {aliquota * 100:.2f}% sul reddito effettivo, nessun contributo minimo dovuto.",
    ]
    if imponibile < P.GESTIONE_SEPARATA["minimale_accredito"]:
        mesi = max(
            1,
            int(12 * imponibile / P.GESTIONE_SEPARATA["minimale_accredito"]),
        ) if imponibile else 0
        note.append(
            f"Reddito sotto il minimale di {P.GESTIONE_SEPARATA['minimale_accredito']:,.0f} euro: "
            f"accrediti circa {mesi} mesi di contribuzione invece di 12."
        )
    if imponibile > P.GESTIONE_SEPARATA["massimale"]:
        note.append(
            f"Reddito oltre il massimale di {P.GESTIONE_SEPARATA['massimale']:,.0f} euro: "
            "l'eccedenza non e' soggetta a contribuzione."
        )

    return Contributi(
        gestione=GESTIONE_SEPARATA,
        imponibile=_arrotonda(imponibile),
        quota_variabile=_arrotonda(imponibile_tassabile * aliquota),
        note=tuple(note),
    )


def artigiani_commercianti(
    imponibile: float,
    *,
    gestione: str = COMMERCIANTI,
    riduzione: int = 0,
    mesi_attivita: int = 12,
    collaboratori: int = 0,
) -> Contributi:
    """Contributi Gestione Artigiani o Commercianti.

    Struttura: quota fissa fino al minimale + percentuale sull'eccedenza,
    con secondo scaglione oltre la soglia annuale.

    riduzione: 0 (nessuna), 35 (forfettari, su tutta la contribuzione),
    50 (prima iscrizione 2025, 36 mesi, solo sulla quota IVS).
    """
    if gestione not in GESTIONI_IMPRESA:
        raise ValueError(f"gestione non valida: {gestione!r}")
    if riduzione not in (0, 35, 50):
        raise ValueError("la riduzione puo' essere 0, 35 o 50")
    if not 1 <= mesi_attivita <= 12:
        raise ValueError("mesi_attivita deve essere compreso tra 1 e 12")

    tabella = P.ARTIGIANI if gestione == ARTIGIANI else P.COMMERCIANTI
    imponibile = max(0.0, imponibile)
    ragguaglio = mesi_attivita / 12

    fisso_pieno = tabella["contributo_fisso"] * ragguaglio
    maternita = P.CONTRIBUTO_MATERNITA * ragguaglio
    minimale = P.MINIMALE_ARTIGIANI_COMMERCIANTI * ragguaglio
    scaglione = P.SCAGLIONE_ARTIGIANI_COMMERCIANTI * ragguaglio
    massimale = P.MASSIMALE_ARTIGIANI_COMMERCIANTI * ragguaglio

    imponibile_utile = min(imponibile, massimale)
    eccedenza_primo = max(0.0, min(imponibile_utile, scaglione) - minimale)
    eccedenza_secondo = max(0.0, imponibile_utile - scaglione)

    variabile_pieno = (
        eccedenza_primo * tabella["aliquota_ivs"]
        + eccedenza_secondo * tabella["aliquota_ivs_oltre_scaglione"]
    )

    note: list[str] = [
        f"Quota fissa dovuta anche a reddito zero: {fisso_pieno:,.2f} euro"
        + (f" (ragguagliata a {mesi_attivita} mesi)" if mesi_attivita != 12 else "")
        + ".",
    ]

    if riduzione == 35:
        fisso = fisso_pieno * (1 - P.RIDUZIONE_35)
        variabile = variabile_pieno * (1 - P.RIDUZIONE_35)
        note.append(
            "Riduzione del 35% riservata ai forfettari: si applica all'intera "
            "contribuzione dovuta. La domanda va presentata entro il 28 febbraio."
        )
    elif riduzione == 50:
        # La riduzione del 50% colpisce la sola quota IVS: la maternita' resta piena.
        ivs_fisso = fisso_pieno - maternita
        fisso = ivs_fisso * (1 - P.RIDUZIONE_50) + maternita
        variabile = variabile_pieno * (1 - P.RIDUZIONE_50)
        note.append(
            "Riduzione del 50% sulla sola quota IVS, valida 36 mesi dall'avvio. "
            "Riservata a chi si e' iscritto per la prima volta nel 2025: dal "
            "1° gennaio 2026 non e' piu' richiedibile da nuovi iscritti."
        )
    else:
        fisso = fisso_pieno
        variabile = variabile_pieno

    if collaboratori:
        note.append(
            f"Sono dovuti anche i contributi per {collaboratori} collaboratore/i "
            "familiare/i: non inclusi in questo calcolo."
        )
    if imponibile > massimale:
        note.append(
            f"Reddito oltre il massimale di {massimale:,.0f} euro: l'eccedenza non e' contribuita."
        )

    totale_pieno = fisso_pieno + variabile_pieno
    totale = fisso + variabile

    return Contributi(
        gestione=gestione,
        imponibile=_arrotonda(imponibile),
        quota_fissa=_arrotonda(fisso),
        quota_variabile=_arrotonda(variabile),
        riduzione_applicata=riduzione,
        risparmio_riduzione=_arrotonda(totale_pieno - totale),
        note=tuple(note),
    )


def calcola(
    imponibile: float,
    *,
    gestione: str,
    riduzione: int = 0,
    mesi_attivita: int = 12,
    gia_assicurato: bool = False,
) -> Contributi:
    """Dispatcher unico usato dai motori di calcolo delle imposte."""
    if gestione == GESTIONE_SEPARATA:
        return gestione_separata(imponibile, gia_assicurato=gia_assicurato)
    if gestione in GESTIONI_IMPRESA:
        return artigiani_commercianti(
            imponibile,
            gestione=gestione,
            riduzione=riduzione,
            mesi_attivita=mesi_attivita,
        )
    if gestione == NESSUNA:
        return Contributi(
            gestione=NESSUNA,
            imponibile=_arrotonda(imponibile),
            note=("Nessun obbligo contributivo previsto per questa posizione.",),
        )
    raise ValueError(f"gestione non gestita: {gestione!r}")


def riduzioni_disponibili(gestione: str, prima_iscrizione_2025: bool = False) -> tuple[int, ...]:
    """Riduzioni contributive effettivamente richiedibili nel 2026."""
    if gestione not in GESTIONI_IMPRESA:
        return (0,)
    if prima_iscrizione_2025:
        return (0, 35, 50)
    return (0, 35)
