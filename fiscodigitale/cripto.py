"""Cripto-attivita' detenute a titolo personale.

Non e' materia da partita IVA: chi investe in proprio produce redditi diversi,
tassati con imposta sostitutiva. E' la confusione piu' diffusa tra chi arriva
al digitale dalla finanza, e il motivo per cui il catalogo include la voce
senza codice ATECO.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import formato
from . import parametri as P


@dataclass(frozen=True)
class EsitoCripto:
    plusvalenza: float
    aliquota: float
    imposta: float
    giacenza_media: float
    imposta_valore: float
    note: tuple[str, ...] = ()

    @property
    def totale_dovuto(self) -> float:
        return round(self.imposta + self.imposta_valore, 2)


def calcola(
    plusvalenza: float,
    *,
    giacenza_media: float = 0.0,
    moneta_elettronica: bool = False,
) -> EsitoCripto:
    """Imposta sulle plusvalenze e imposta sul valore delle cripto-attivita'.

    moneta_elettronica: token ancorati all'euro conformi a MiCAR, che
    mantengono l'aliquota piu' bassa.
    """
    plusvalenza = max(0.0, plusvalenza)
    aliquota = (
        P.CRIPTO["aliquota_emt_micar"] if moneta_elettronica else P.CRIPTO["aliquota_plusvalenze"]
    )
    imposta = round(plusvalenza * aliquota, 2)
    imposta_valore = round(max(0.0, giacenza_media) * P.CRIPTO["imposta_valore_cripto"], 2)

    note = [
        f"Aliquota {formato.percentuale(aliquota, 0)} sulle plusvalenze realizzate.",
        f"Nessuna soglia di esenzione: e' stata abolita, anche pochi euro di "
        "plusvalenza sono imponibili.",
        f"Le cripto-attivita' vanno indicate nel {P.CRIPTO['quadro_dichiarativo']}.",
    ]
    if imposta_valore:
        note.append(
            f"Imposta sul valore delle cripto-attivita' del "
            f"{P.CRIPTO['imposta_valore_cripto'] * 1000:.0f} per mille: "
            f"{formato.euro(imposta_valore, 2)}."
        )
    if moneta_elettronica:
        note.append(
            "Aliquota ridotta riservata ai token di moneta elettronica ancorati "
            "all'euro: verifica che rientrino davvero nella categoria."
        )

    return EsitoCripto(
        plusvalenza=round(plusvalenza, 2),
        aliquota=aliquota,
        imposta=imposta,
        giacenza_media=round(max(0.0, giacenza_media), 2),
        imposta_valore=imposta_valore,
        note=tuple(note),
    )
