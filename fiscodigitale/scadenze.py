"""Scadenzario fiscale e contributivo personalizzato.

Le scadenze cambiano in base a regime, gestione previdenziale e presenza di
operazioni estere: un calendario generico e' rumore, questo e' filtrato.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from . import parametri as P
from . import previdenza

FISCALE = "Imposte"
CONTRIBUTI = "Contributi"
IVA = "IVA ed estero"
ADEMPIMENTI = "Adempimenti"


@dataclass(frozen=True)
class Scadenza:
    data: date
    titolo: str
    descrizione: str
    categoria: str
    ricorrente: bool = False

    @property
    def etichetta(self) -> str:
        return f"{self.data.strftime('%d/%m/%Y')} - {self.titolo}"

    def giorni_mancanti(self, oggi: date | None = None) -> int:
        return (self.data - (oggi or date.today())).days


@dataclass(frozen=True)
class Profilo:
    """Profilo minimo necessario a filtrare le scadenze."""

    regime: str = "forfettario"
    gestione: str = previdenza.GESTIONE_SEPARATA
    acquisti_esteri: bool = False
    vendite_ue_b2b: bool = False
    riduzione_contributiva_da_chiedere: bool = False
    oss: bool = False
    soggetto_isa: bool = False
    periodicita_intrastat: str | None = None

    def __post_init__(self):
        if self.periodicita_intrastat not in (None, "mensile", "trimestrale"):
            raise ValueError("periodicita INTRASTAT non valida")


def _giorno_lavorativo(giorno: date) -> date:
    """Sposta al primo giorno feriale successivo (sabato e domenica)."""
    # Festivita nazionali; lunedi di Pasqua calcolato con algoritmo gregoriano.
    y = giorno.year
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    pasqua = date(y, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)
    festivi = {date(y, mo, dy) for mo, dy in ((1,1),(1,6),(4,25),(5,1),(6,2),(8,15),(11,1),(12,8),(12,25),(12,26))}
    festivi.add(pasqua + timedelta(days=1))
    while giorno.weekday() >= 5 or giorno in festivi:
        giorno += timedelta(days=1)
    return giorno


def calendario(anno: int = P.ANNO_IMPOSTA, profilo: Profilo | None = None) -> tuple[Scadenza, ...]:
    """Genera lo scadenzario dell'anno per il profilo indicato."""
    p = profilo or Profilo()
    scadenze: list[Scadenza] = []

    def aggiungi(giorno: date, titolo: str, descrizione: str, categoria: str,
                 ricorrente: bool = False, *, sposta_weekend: bool = True) -> None:
        scadenze.append(
            Scadenza(_giorno_lavorativo(giorno) if sposta_weekend else giorno,
                     titolo, descrizione, categoria, ricorrente)
        )

    # La proroga 2026 e verificata separatamente: non estenderla agli altri anni.
    saldo = date(anno, 7, 20) if anno == 2026 and p.soggetto_isa else date(anno, 6, 30)
    prima, seconda = (50, 50) if p.soggetto_isa else (40, 60)
    differimento = ("20 agosto con maggiorazione dello 0,80%" if anno == 2026 and p.soggetto_isa
                    else "30 luglio con maggiorazione dello 0,40%")
    # --- Imposte -----------------------------------------------------------
    aggiungi(
        saldo,
        "Saldo imposte e primo acconto",
        f"Saldo dell'anno precedente e prima rata di acconto ({prima}%). "
        f"Differimento al {differimento}. Verificare requisiti e proroghe annuali.",
        FISCALE,
    )
    aggiungi(
        date(anno, 11, 30),
        "Secondo acconto",
        f"Seconda rata di acconto ({seconda}%) delle imposte sui redditi.",
        FISCALE,
    )
    aggiungi(
        date(anno, 10, 31),
        "Dichiarazione dei redditi",
        "Invio telematico del modello Redditi PF relativo all'anno precedente.",
        ADEMPIMENTI,
    )

    # --- Contributi --------------------------------------------------------
    if p.gestione in previdenza.GESTIONI_IMPRESA:
        for giorno, etichetta in (
            (date(anno, 5, 16), "prima"),
            (date(anno, 8, 20), "seconda"),
            (date(anno, 11, 16), "terza"),
            (date(anno + 1, 2, 16), "quarta"),
        ):
            aggiungi(
                giorno,
                f"Contributi INPS fissi - {etichetta} rata",
                "Rata trimestrale della quota fissa sul reddito minimale, dovuta "
                "anche in assenza di reddito.",
                CONTRIBUTI,
            )
        aggiungi(
            saldo,
            "Saldo e primo acconto contributi eccedenti",
            "Quota percentuale sul reddito oltre il minimale: saldo dell'anno "
            "precedente e primo acconto.",
            CONTRIBUTI,
        )
        aggiungi(date(anno, 11, 30), "Secondo acconto contributi eccedenti",
                 "Seconda rata di acconto sulla quota eccedente il minimale.", CONTRIBUTI)
        if p.riduzione_contributiva_da_chiedere:
            aggiungi(
                date(anno, 2, 28),
                "Domanda di riduzione contributiva del 35%",
                "Termine perentorio per i forfettari che vogliono la riduzione del "
                "35% per attivita gia esistenti che accedono per la prima volta. "
                "Chi gia beneficia non rinnova; nuove aperture: domanda tempestiva dopo iscrizione.",
                CONTRIBUTI,
            )
    else:
        aggiungi(
            saldo,
            "Saldo e primo acconto Gestione Separata",
            "I contributi della Gestione Separata seguono le scadenze delle imposte: "
            "saldo dell'anno precedente piu' meta dell'acconto dell'80% (40% del contributo storico).",
            CONTRIBUTI,
        )
        aggiungi(
            date(anno, 11, 30),
            "Secondo acconto Gestione Separata",
            "Seconda rata di acconto contributivo.",
            CONTRIBUTI,
        )

    # --- IVA ed estero -----------------------------------------------------
    if p.acquisti_esteri:
        for mese in range(1, 13):
            aggiungi(
                date(anno, mese, 20 if mese == 8 else 16),
                "Versamento IVA da inversione contabile",
                "Versamento con F24 dell'IVA sugli acquisti esteri del mese "
                "precedente. Nel forfettario non e' detraibile.",
                IVA,
                ricorrente=True,
            )
            aggiungi(
                date(anno, mese, 15),
                "Integrazione delle fatture estere",
                "Trasmissione via SDI dei documenti TD17, TD18 o TD19 relativi agli "
                "acquisti del mese precedente.",
                IVA,
                ricorrente=True,
            )
    if p.vendite_ue_b2b and p.periodicita_intrastat:
        mesi_intrastat = range(1, 13) if p.periodicita_intrastat == "mensile" else (1, 4, 7, 10)
        for mese in mesi_intrastat:
            aggiungi(
                date(anno, mese, 25),
                "Elenchi INTRASTAT",
                "Riepilogo dei servizi resi a soggetti passivi UE del periodo precedente.",
                IVA,
                ricorrente=True,
            )
    if p.oss:
        for mese, trimestre in ((4, "primo"), (7, "secondo"), (10, "terzo"), (1, "quarto")):
            anno_effettivo = anno + 1 if mese == 1 else anno
            aggiungi(
                date(anno_effettivo, mese, monthrange(anno_effettivo, mese)[1]),
                f"Dichiarazione OSS - {trimestre} trimestre",
                "Dichiarazione e versamento dell'IVA dovuta negli altri Stati UE. "
                "Termine all'ultimo giorno del mese successivo al trimestre, "
                "senza rinvio per sabato, domenica o festivita'.",
                IVA,
                sposta_weekend=False,
            )
    if p.regime != "forfettario":
        aggiungi(
            date(anno, 4, 30),
            "Dichiarazione IVA annuale",
            "Presentazione della dichiarazione IVA relativa all'anno precedente.",
            ADEMPIMENTI,
        )
        for giorno, periodo in (
            (date(anno, 5, 31), "primo trimestre"),
            (date(anno, 9, 30), "secondo trimestre"),
            (date(anno, 11, 30), "terzo trimestre"),
            (date(anno + 1, 2, 28), "quarto trimestre"),
        ):
            aggiungi(
                giorno,
                f"LIPE - {periodo}",
                "Comunicazione delle liquidazioni periodiche IVA.",
                ADEMPIMENTI,
            )

    # --- Bollo virtuale ----------------------------------------------------
    for mese, trimestre in ((5, "primo"), (9, "secondo"), (11, "terzo"), (2, "quarto")):
        anno_effettivo = anno + 1 if mese == 2 else anno
        aggiungi(
            date(anno_effettivo, mese, 31 if mese in (5,) else 30 if mese in (9, 11) else 28),
            f"Imposta di bollo sulle fatture - {trimestre} trimestre",
            f"Versamento del bollo da {P.IMPOSTA_BOLLO:.2f} euro applicato alle "
            f"fatture senza IVA oltre {P.SOGLIA_BOLLO:.2f} euro.",
            ADEMPIMENTI,
        )

    scadenze.sort(key=lambda s: (s.data, s.categoria, s.titolo))
    return tuple(scadenze)


def prossime(
    quante: int = 5,
    *,
    da: date | None = None,
    profilo: Profilo | None = None,
) -> tuple[Scadenza, ...]:
    """Prossime scadenze a partire da una data (default: oggi).

    Include anche il calendario dell'anno precedente: alcune scadenze di un
    anno cadono in quello successivo, come la quarta rata fissa di artigiani e
    commercianti a febbraio, che a gennaio sarebbe la prima in arrivo.
    """
    oggi = da or date.today()
    tutte = (
        calendario(oggi.year - 1, profilo)
        + calendario(oggi.year, profilo)
        + calendario(oggi.year + 1, profilo)
    )
    viste: set[tuple[date, str]] = set()
    future: list[Scadenza] = []
    for s in sorted(tutte, key=lambda x: (x.data, x.titolo)):
        chiave = (s.data, s.titolo)
        if s.data >= oggi and chiave not in viste:
            viste.add(chiave)
            future.append(s)
    return tuple(future[:quante])

