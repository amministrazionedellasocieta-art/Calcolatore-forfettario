"""Confronto forfettario contro ordinario e ricerca del punto di pareggio.

La domanda giusta non e' "quanto pago in forfettario" ma "da quanti costi in
poi il forfettario mi sta facendo perdere soldi". Con i coefficienti bassi
(commercio al 40%) il forfettario e' quasi sempre meglio; con quelli alti
(78%, 86%) chi ha costi reali importanti perde.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import forfettario, ordinario, previdenza


@dataclass(frozen=True)
class Confronto:
    ricavi: float
    costi: float
    esito_forfettario: forfettario.Esito
    esito_ordinario: ordinario.EsitoOrdinario
    costi_di_pareggio: float | None
    quota_costi_di_pareggio: float | None

    @property
    def netto_forfettario(self) -> float:
        """Netto reale: nel forfettario i costi si sostengono ma non si deducono."""
        return round(self.esito_forfettario.netto - self.costi, 2)

    @property
    def netto_ordinario(self) -> float:
        return self.esito_ordinario.netto

    @property
    def differenza(self) -> float:
        """Positiva se conviene il forfettario."""
        return round(self.netto_forfettario - self.netto_ordinario, 2)

    @property
    def conviene(self) -> str:
        if abs(self.differenza) < 1:
            return "pari"
        return "forfettario" if self.differenza > 0 else "ordinario"

    @property
    def sintesi(self) -> str:
        if self.conviene == "pari":
            return "I due regimi si equivalgono con questi numeri."
        vincitore = "forfettario" if self.conviene == "forfettario" else "regime ordinario"
        testo = (
            f"Con {self.costi:,.0f} euro di costi reali conviene il {vincitore}: "
            f"{abs(self.differenza):,.0f} euro di differenza netta all'anno."
        )
        if self.costi_di_pareggio:
            testo += (
                f" Il pareggio e' a {self.costi_di_pareggio:,.0f} euro di costi "
                f"({(self.quota_costi_di_pareggio or 0) * 100:.0f}% dei ricavi)."
            )
        return testo


def confronta(
    situazione: forfettario.Situazione,
    costi: float = 0.0,
    *,
    addizionale_regionale: float | None = None,
    addizionale_comunale: float | None = None,
) -> Confronto:
    """Confronta i due regimi a parita' di ricavi e costi reali."""
    esito_f = forfettario.calcola(situazione)

    kwargs = {}
    if addizionale_regionale is not None:
        kwargs["addizionale_regionale"] = addizionale_regionale
    if addizionale_comunale is not None:
        kwargs["addizionale_comunale"] = addizionale_comunale

    situazione_o = ordinario.SituazioneOrdinario(
        ricavi=situazione.ricavi,
        costi=costi,
        gestione=situazione.gestione,
        mesi_attivita=situazione.mesi_attivita,
        gia_assicurato=situazione.gia_assicurato,
        **kwargs,
    )
    esito_o = ordinario.calcola(situazione_o)

    pareggio = costi_di_pareggio(situazione, **kwargs)
    quota = (pareggio / situazione.ricavi) if (pareggio and situazione.ricavi) else None

    return Confronto(
        ricavi=situazione.ricavi,
        costi=costi,
        esito_forfettario=esito_f,
        esito_ordinario=esito_o,
        costi_di_pareggio=pareggio,
        quota_costi_di_pareggio=round(quota, 4) if quota is not None else None,
    )


def costi_di_pareggio(
    situazione: forfettario.Situazione,
    *,
    addizionale_regionale: float | None = None,
    addizionale_comunale: float | None = None,
    tolleranza: float = 1.0,
) -> float | None:
    """Livello di costi reali oltre il quale l'ordinario batte il forfettario.

    None se il forfettario resta migliore anche azzerando il reddito.
    """
    if situazione.ricavi <= 0:
        return None

    # A parita' di costi reali, il confronto si riduce al totale di imposte e
    # contributi: i costi si sostengono in entrambi i regimi, cambia solo se
    # sono deducibili.
    dovuto_forfettario = forfettario.calcola(situazione).totale_dovuto

    kwargs = {}
    if addizionale_regionale is not None:
        kwargs["addizionale_regionale"] = addizionale_regionale
    if addizionale_comunale is not None:
        kwargs["addizionale_comunale"] = addizionale_comunale

    def dovuto_ordinario(costi: float) -> float:
        return ordinario.calcola(
            ordinario.SituazioneOrdinario(
                ricavi=situazione.ricavi,
                costi=costi,
                gestione=situazione.gestione,
                mesi_attivita=situazione.mesi_attivita,
                gia_assicurato=situazione.gia_assicurato,
                **kwargs,
            )
        ).totale_dovuto

    # Il dovuto in ordinario decresce all'aumentare dei costi deducibili.
    if dovuto_ordinario(0.0) <= dovuto_forfettario:
        return 0.0  # l'ordinario conviene gia' senza alcun costo
    if dovuto_ordinario(situazione.ricavi) > dovuto_forfettario:
        return None  # il forfettario resta migliore in ogni scenario

    basso, alto = 0.0, situazione.ricavi
    for _ in range(200):
        medio = (basso + alto) / 2
        valore = dovuto_ordinario(medio)
        if abs(valore - dovuto_forfettario) <= tolleranza:
            return round(medio, 2)
        if valore > dovuto_forfettario:
            basso = medio
        else:
            alto = medio
    return round((basso + alto) / 2, 2)
