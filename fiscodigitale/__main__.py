"""Riga di comando: una diagnosi fiscale senza aprire il browser.

    python3 -m fiscodigitale --cerca streamer
    python3 -m fiscodigitale --professione streamer --ricavi 40000 --costi 5000
"""

from __future__ import annotations

import argparse

from . import diagnosi, professioni
from . import parametri as P


def _euro(valore: float) -> str:
    return f"{valore:,.0f} euro".replace(",", ".")


def _riga(titolo: str) -> None:
    print()
    print(titolo)
    print("-" * len(titolo))


def _elenca(elenco) -> None:
    for p in elenco:
        print(f"  {p.slug:<22} {p.nome[:44]:<46} ATECO {p.ateco or '-':<10} {p.coefficiente_pct}%")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fiscodigitale",
        description=f"Fiscalita' dei lavori digitali - anno d'imposta {P.ANNO_IMPOSTA}",
    )
    parser.add_argument("--cerca", help="cerca una professione nel catalogo")
    parser.add_argument("--professione", help="slug della professione da analizzare")
    parser.add_argument("--ricavi", type=float, default=40_000, help="ricavi annui attesi")
    parser.add_argument("--costi", type=float, default=0.0, help="costi reali annui")
    parser.add_argument("--esteri", type=float, default=0.0,
                        help="acquisti annui di servizi esteri")
    parser.add_argument("--altra", action="append", default=[], metavar="SLUG:RICAVI",
                        help="altra fonte di ricavo con codice ATECO diverso, "
                             "ripetibile (es. --altra youtuber:15000)")
    parser.add_argument("--natura", choices=(diagnosi.PROFESSIONALE, diagnosi.IMPRESA),
                        help="come eserciti: professionale o impresa. Rilevante solo "
                             "per i lavori il cui inquadramento non e' univoco")
    parser.add_argument("--non-startup", action="store_true",
                        help="non applicare l'aliquota agevolata al 5 per cento")
    parser.add_argument("--elenco", action="store_true", help="elenca tutte le professioni")
    args = parser.parse_args(argv)

    if args.elenco or (not args.professione and not args.cerca):
        _riga(f"Catalogo ({len(professioni.CATALOGO)} professioni)")
        for categoria in professioni.CATEGORIE:
            print(f"\n{categoria}")
            _elenca(professioni.per_categoria(categoria))
        return 0

    if args.cerca:
        risultati = professioni.cerca(args.cerca)
        _riga(f"Risultati per '{args.cerca}'")
        if not risultati:
            print("Nessuna corrispondenza.")
            return 1
        _elenca(risultati)
        if not args.professione:
            return 0

    altre = []
    for voce in args.altra:
        if ":" not in voce:
            parser.error(f"formato non valido per --altra: {voce!r} (atteso SLUG:RICAVI)")
        altro_slug, _, importo = voce.partition(":")
        try:
            altre.append(diagnosi.AltraAttivita(altro_slug.strip(), float(importo)))
        except (ValueError, KeyError) as errore:
            parser.error(f"--altra {voce!r}: {errore}")

    slug = args.professione or professioni.cerca(args.cerca)[0].slug
    esito = diagnosi.analizza(
        diagnosi.Profilo(
            professione=slug,
            ricavi_attesi=args.ricavi,
            costi_annui=args.costi,
            acquisti_servizi_esteri=args.esteri,
            clienti_esteri_b2b=args.esteri > 0,
            prima_attivita=not args.non_startup,
            natura_attivita=args.natura,
            altre_attivita=tuple(altre),
        )
    )

    _riga(esito.professione.nome)
    print(esito.sintesi())

    if esito.multi_attivita:
        _riga("Attivita'")
        for a in esito.attivita:
            print(f"  {a.professione.nome[:34]:<36} {_euro(a.ricavi):>14}  "
                  f"x {a.professione.coefficiente_pct}%  = {_euro(a.reddito)}")

    _riga("Requisiti")
    for v in esito.verifiche:
        simbolo = {"ok": "[ok]", "attenzione": "[!]", "bloccante": "[X]"}[v.esito]
        print(f"{simbolo} {v.nome}: {v.messaggio}")

    _riga("Numeri")
    e = esito.esito_forfettario
    print(f"Reddito forfetario      {_euro(e.reddito_forfetario)}")
    print(f"Imposta sostitutiva     {_euro(e.imposta_sostitutiva)}")
    print(f"Contributi INPS         {_euro(e.contributi_dovuti)}")
    print(f"Pressione effettiva     {e.pressione_effettiva * 100:.1f}%")
    print(f"Netto reale             {_euro(esito.netto_reale)}")
    print(f"Da accantonare          {e.accantonamento_consigliato * 100:.0f}% di ogni incasso")

    _riga("Cassa dei primi anni")
    for anno in esito.piano_cassa:
        print(f"{anno.anno}  uscite {_euro(anno.uscite_cassa):>16}  "
              f"(imposte {_euro(anno.imposta_cassa)}, contributi {_euro(anno.contributi_cassa)})")

    _riga("Confronto con l'ordinario")
    print(esito.confronto_regimi.sintesi)

    _riga("Adempimenti")
    for i, a in enumerate(esito.adempimenti, start=1):
        print(f"{i}. {a.titolo} - {a.quando}")

    if esito.avvisi:
        _riga("Da sapere")
        for a in esito.avvisi:
            print(f"- {a}")

    _riga("Prossime scadenze")
    for s in esito.prossime_scadenze:
        print(f"{s.data.strftime('%d/%m/%Y')}  {s.titolo}")

    print()
    print("Stime a scopo informativo: l'inquadramento va confermato con un commercialista.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
