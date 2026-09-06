"""Scadenzario fiscale e contributivo personalizzato.

Le scadenze cambiano in base a regime, gestione previdenziale e presenza di
operazioni estere: un calendario generico e' rumore, questo e' filtrato.
"""

from __future__ import annotations

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


def _giorno_lavorativo(giorno: date) -> date:
    """Sposta al primo giorno feriale successivo (sabato e domenica)."""
    while giorno.weekday() >= 5:
        giorno += timedelta(days=1)
    return giorno


def calendario(anno: int = P.ANNO_IMPOSTA, profilo: Profilo | None = None) -> tuple[Scadenza, ...]:
    """Genera lo scadenzario dell'anno per il profilo indicato."""
    p = profilo or Profilo()
    scadenze: list[Scadenza] = []

    def aggiungi(giorno: date, titolo: str, descrizione: str, categoria: str,
                 ricorrente: bool = False) -> None:
        scadenze.append(
            Scadenza(_giorno_lavorativo(giorno), titolo, descrizione, categoria, ricorrente)
        )

    # --- Imposte -----------------------------------------------------------
    aggiungi(
        date(anno, 6, 30),
        "Saldo imposte e primo acconto",
        "Saldo dell'anno precedente e prima rata di acconto (40%). E' possibile "
        "versare entro il 30 luglio con una maggiorazione dello 0,40%.",
        FISCALE,
    )
    aggiungi(
        date(anno, 11, 30),
        "Secondo acconto",
        "Seconda rata di acconto (60%) delle imposte sui redditi.",
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
            date(anno, 6, 30),
            "Saldo e primo acconto contributi eccedenti",
            "Quota percentuale sul reddito oltre il minimale: saldo dell'anno "
            "precedente e primo acconto.",
            CONTRIBUTI,
        )
        if p.riduzione_contributiva_da_chiedere:
            aggiungi(
                date(anno, 2, 28),
                "Domanda di riduzione contributiva del 35%",
                "Termine perentorio per i forfettari che vogliono la riduzione del "
                "35% per l'anno in corso. Chi non presenta la domanda paga per intero.",
                CONTRIBUTI,
            )
    else:
        aggiungi(
            date(anno, 6, 30),
            "Saldo e primo acconto Gestione Separata",
            "I contributi della Gestione Separata seguono le scadenze delle imposte: "
            "saldo dell'anno precedente piu' primo acconto (40% dell'80% dovuto).",
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
                date(anno, mese, 16),
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
    if p.vendite_ue_b2b:
        for mese in range(1, 13):
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
                date(anno_effettivo, mese, 30 if mese != 1 else 31),
                f"Dichiarazione OSS - {trimestre} trimestre",
                "Dichiarazione e versamento dell'IVA dovuta negli altri Stati UE.",
                IVA,
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
    """Prossime scadenze a partire da una data (default: oggi)."""
    oggi = da or date.today()
    tutte = calendario(oggi.year, profilo) + calendario(oggi.year + 1, profilo)
    future = [s for s in tutte if s.data >= oggi]
    return tuple(future[:quante])
