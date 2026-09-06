"""Contabilita' di cassa e presidio delle soglie.

Il forfettario non tiene le scritture contabili, ma deve comunque sapere in
ogni momento tre cose: a che punto e' rispetto alle soglie, quanto deve
accantonare e quanta IVA estera ha maturato. Questo modulo risponde a tutte e
tre partendo da un semplice registro di incassi e spese.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import forfettario, iva_estero
from . import parametri as P

INCASSO = "incasso"
SPESA = "spesa"


@dataclass(frozen=True)
class Movimento:
    data: date
    descrizione: str
    importo: float
    tipo: str = INCASSO
    area: str = iva_estero.ITALIA
    controparte: str = iva_estero.B2B
    oggetto: str = iva_estero.SERVIZIO
    categoria: str = ""

    def __post_init__(self) -> None:
        if self.importo < 0:
            raise ValueError("l'importo va indicato in valore assoluto")
        if self.tipo not in (INCASSO, SPESA):
            raise ValueError(f"tipo non valido: {self.tipo!r}")

    @property
    def iva_reverse_charge(self) -> float:
        """IVA da versare se si tratta di un acquisto estero di servizi o beni."""
        if self.tipo != SPESA or self.area == iva_estero.ITALIA:
            return 0.0
        return iva_estero.iva_reverse_charge(self.importo)


@dataclass(frozen=True)
class Soglia:
    nome: str
    valore_corrente: float
    limite: float
    descrizione: str
    conseguenza: str

    @property
    def percentuale(self) -> float:
        if self.limite <= 0:
            return 0.0
        return min(2.0, self.valore_corrente / self.limite)

    @property
    def stato(self) -> str:
        pct = self.percentuale
        if pct >= 1:
            return "superata"
        if pct >= 0.9:
            return "critica"
        if pct >= 0.7:
            return "attenzione"
        return "ok"

    @property
    def residuo(self) -> float:
        return round(max(0.0, self.limite - self.valore_corrente), 2)


class Registro:
    """Registro di cassa con proiezioni e controllo delle soglie."""

    def __init__(self, anno: int = P.ANNO_IMPOSTA, movimenti: list[Movimento] | None = None):
        self.anno = anno
        self.movimenti: list[Movimento] = list(movimenti or [])

    # -- alimentazione ---------------------------------------------------
    def aggiungi(self, movimento: Movimento) -> "Registro":
        if movimento.data.year != self.anno:
            raise ValueError(
                f"il movimento del {movimento.data} non appartiene all'anno {self.anno}"
            )
        self.movimenti.append(movimento)
        return self

    # -- totali ----------------------------------------------------------
    @property
    def incassi(self) -> float:
        return round(sum(m.importo for m in self.movimenti if m.tipo == INCASSO), 2)

    @property
    def spese(self) -> float:
        return round(sum(m.importo for m in self.movimenti if m.tipo == SPESA), 2)

    @property
    def vendite_ue_b2c(self) -> float:
        return round(
            sum(
                m.importo
                for m in self.movimenti
                if m.tipo == INCASSO
                and m.area == iva_estero.UE
                and m.controparte == iva_estero.B2C
            ),
            2,
        )

    @property
    def acquisti_beni_ue(self) -> float:
        return round(
            sum(
                m.importo
                for m in self.movimenti
                if m.tipo == SPESA
                and m.area == iva_estero.UE
                and m.oggetto == iva_estero.BENE
            ),
            2,
        )

    @property
    def iva_reverse_charge_maturata(self) -> float:
        return round(sum(m.iva_reverse_charge for m in self.movimenti), 2)

    def incassi_per_mese(self) -> dict[int, float]:
        totali = {mese: 0.0 for mese in range(1, 13)}
        for m in self.movimenti:
            if m.tipo == INCASSO:
                totali[m.data.month] = round(totali[m.data.month] + m.importo, 2)
        return totali

    def iva_reverse_charge_per_mese(self) -> dict[int, float]:
        totali = {mese: 0.0 for mese in range(1, 13)}
        for m in self.movimenti:
            if m.iva_reverse_charge:
                totali[m.data.month] = round(totali[m.data.month] + m.iva_reverse_charge, 2)
        return totali

    # -- proiezioni ------------------------------------------------------
    def proiezione_annuale(self, al: date | None = None) -> float:
        """Stima dei ricavi di fine anno sulla base del ritmo attuale."""
        riferimento = al or date.today()
        if riferimento.year != self.anno:
            return self.incassi
        giorni_trascorsi = (riferimento - date(self.anno, 1, 1)).days + 1
        if giorni_trascorsi <= 0 or self.incassi == 0:
            return self.incassi
        giorni_anno = 366 if self.anno % 4 == 0 and (self.anno % 100 != 0 or self.anno % 400 == 0) else 365
        return round(self.incassi * giorni_anno / giorni_trascorsi, 2)

    def soglie(self, al: date | None = None, costo_personale: float = 0.0) -> tuple[Soglia, ...]:
        proiezione = self.proiezione_annuale(al)
        return (
            Soglia(
                nome="Permanenza nel forfettario",
                valore_corrente=self.incassi,
                limite=P.SOGLIA_RICAVI,
                descrizione=f"Incassi dell'anno rispetto al limite di {P.SOGLIA_RICAVI:,.0f} euro "
                            f"(proiezione a fine anno: {proiezione:,.0f} euro).",
                conseguenza="Superandola resti in forfettario quest'anno ma passi "
                            "all'ordinario dal prossimo.",
            ),
            Soglia(
                nome="Uscita immediata dal regime",
                valore_corrente=self.incassi,
                limite=P.SOGLIA_USCITA_IMMEDIATA,
                descrizione="Oltre questo importo il regime decade nell'anno stesso.",
                conseguenza="Dovrai applicare l'IVA su tutte le operazioni dell'anno, "
                            "comprese quelle gia' fatturate.",
            ),
            Soglia(
                nome="Vendite a privati UE (OSS)",
                valore_corrente=self.vendite_ue_b2c,
                limite=P.SOGLIA_OSS,
                descrizione="Cumulo annuo di vendite a distanza e servizi digitali "
                            "verso consumatori di altri Paesi UE.",
                conseguenza="Oltre la soglia si applica l'IVA del Paese del cliente, "
                            "con registrazione al regime OSS.",
            ),
            Soglia(
                nome="Acquisti di beni UE",
                valore_corrente=self.acquisti_beni_ue,
                limite=P.SOGLIA_OSS,
                descrizione="Cumulo annuo degli acquisti intracomunitari di beni.",
                conseguenza="Oltre la soglia diventano acquisti intracomunitari veri: "
                            "servono VIES, integrazione e versamento dell'IVA.",
            ),
            Soglia(
                nome="Costo del personale",
                valore_corrente=costo_personale,
                limite=P.LIMITE_SPESE_PERSONALE,
                descrizione="Spese per dipendenti, collaboratori e lavoro accessorio.",
                conseguenza="Superandola si perde il requisito di accesso al regime.",
            ),
        )

    def allerte(self, al: date | None = None, costo_personale: float = 0.0) -> tuple[str, ...]:
        messaggi: list[str] = []
        for soglia in self.soglie(al, costo_personale):
            if soglia.stato == "superata":
                messaggi.append(f"[SUPERATA] {soglia.nome}: {soglia.conseguenza}")
            elif soglia.stato == "critica":
                messaggi.append(
                    f"[CRITICA] {soglia.nome}: mancano {soglia.residuo:,.0f} euro al limite."
                )
        proiezione = self.proiezione_annuale(al)
        if proiezione > P.SOGLIA_RICAVI >= self.incassi:
            messaggi.append(
                f"[PROIEZIONE] Con questo ritmo chiuderai a {proiezione:,.0f} euro e "
                f"superarai il limite di {P.SOGLIA_RICAVI:,.0f}: valuta ora come gestire "
                "gli incassi di fine anno."
            )
        if self.iva_reverse_charge_maturata > 0:
            messaggi.append(
                f"[IVA] Hai maturato {self.iva_reverse_charge_maturata:,.2f} euro di IVA "
                "su acquisti esteri da versare con F24."
            )
        return tuple(messaggi)

    # -- accantonamento --------------------------------------------------
    def accantonamento(
        self,
        situazione: forfettario.Situazione,
        al: date | None = None,
    ) -> dict[str, float]:
        """Quanto mettere da parte, calcolato sulla proiezione di fine anno."""
        from dataclasses import replace

        proiezione = max(self.proiezione_annuale(al), self.incassi)
        esito = forfettario.calcola(replace(situazione, ricavi=proiezione))
        quota = esito.pressione_effettiva
        return {
            "proiezione_ricavi": proiezione,
            "imposte_e_contributi_stimati": esito.totale_dovuto,
            "quota_su_ogni_incasso": round(quota, 4),
            "da_accantonare_ora": round(self.incassi * quota, 2),
            "iva_estera_da_versare": self.iva_reverse_charge_maturata,
        }
