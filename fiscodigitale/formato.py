"""Formattazione dei numeri secondo le convenzioni italiane.

Python separa le migliaia con la virgola e i decimali con il punto: l'opposto
di come si scrivono gli importi in italiano. Senza questo modulo i messaggi
del motore mostravano "7,860 euro" dove l'interfaccia scriveva "7.860".
"""

from __future__ import annotations


def numero(valore: float, decimali: int = 0) -> str:
    """Formatta un numero all'italiana: 7.860,25 invece di 7,860.25."""
    grezzo = f"{valore:,.{decimali}f}"
    return grezzo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def euro(valore: float, decimali: int = 0) -> str:
    """Importo con l'unita': "7.860 euro"."""
    return f"{numero(valore, decimali)} euro"


def percentuale(valore: float, decimali: int = 1) -> str:
    """Percentuale da una frazione: 0.2607 diventa "26,1%"."""
    return f"{valore * 100:.{decimali}f}".replace(".", ",") + "%"
