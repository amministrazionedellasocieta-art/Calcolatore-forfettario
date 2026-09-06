"""Fisco Digitale - motore di fiscalita' e contabilita' per i lavori digitali.

Il pacchetto e' indipendente dall'interfaccia: nessun modulo importa Streamlit,
cosi' lo stesso motore serve l'app, la riga di comando o una futura API.

Esempio:

    from fiscodigitale import diagnosi

    esito = diagnosi.analizza(
        diagnosi.Profilo(professione="streamer", ricavi_attesi=40_000)
    )
    print(esito.sintesi())
"""

from . import (  # noqa: F401
    confronto,
    contabilita,
    diagnosi,
    forfettario,
    iva_estero,
    ordinario,
    parametri,
    previdenza,
    professioni,
    scadenze,
)

__version__ = "1.0.0"
ANNO_IMPOSTA = parametri.ANNO_IMPOSTA

__all__ = [
    "confronto",
    "contabilita",
    "diagnosi",
    "forfettario",
    "iva_estero",
    "ordinario",
    "parametri",
    "previdenza",
    "professioni",
    "scadenze",
    "ANNO_IMPOSTA",
    "__version__",
]
