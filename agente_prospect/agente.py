"""Agente di ricerca: mappa le pagine pubbliche di giovani che lavorano nel digitale
(freelance, creator, social media manager, sviluppatori, designer...) per individuare
opportunità di collaborazione e di presenza per Fisco Chiaro Consulting.

L'agente NON raccoglie email, numeri di telefono o altri dati di contatto personali e
NON invia messaggi: produce un elenco di pagine da valutare a mano. Vedi README.md per i
limiti normativi (GDPR, art. 130 Codice privacy, linee guida Garante sullo spam).

Uso:
    export ANTHROPIC_API_KEY=...
    python agente.py --nicchia "social media manager" --citta Milano --max 20
"""

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

import anthropic

MODEL = "claude-opus-5-5"
OUTPUT_DIR = Path(__file__).parent / "output"
CSV_PATH = OUTPUT_DIR / "pagine_trovate.csv"
MAX_CONTINUAZIONI = 8

CAMPI = [
    "nome",
    "url",
    "piattaforma",
    "categoria",
    "tipo_pagina",
    "opportunita",
    "motivo",
    "pagina_collaborazioni",
    "nicchia_ricerca",
    "data_ricerca",
]

SYSTEM = """Sei un ricercatore di mercato per Fisco Chiaro Consulting (https://www.fiscochiaroconsulting.it), \
servizio di consulenza fiscale e contabile personalizzata per professionisti, freelance, ditte individuali e imprese in Italia, inclusi contribuenti forfettari e attivita digitali. Offre assistenza continuativa, adempimenti, valutazioni sul regime fiscale e supporto alla crescita dell'attivita.

Obiettivo: trovare sul web pagine PUBBLICHE e PROFESSIONALI di giovani (indicativamente under 35) \
che lavorano nel digitale in Italia - freelance, creator, social media manager, web designer, \
sviluppatori, copywriter, video editor, community e newsletter del settore - utili a Fisco Chiaro per:
- "collaborazione": creator o professionisti che dichiarano pubblicamente di accettare \
collaborazioni/partnership (es. contenuti divulgativi su P.IVA e forfettario);
- "community": gruppi, community, eventi, newsletter, podcast frequentati dal target, dove \
Fisco Chiaro può essere presente con contenuti utili;
- "contenuti": pagine che mostrano dubbi fiscali ricorrenti del target, utili come spunti editoriali.

Regole obbligatorie:
1. Considera solo pagine professionali/pubbliche (siti portfolio, pagine business, canali, \
community). Escludi profili privati, minorenni e contenuti personali.
2. NON estrarre, riportare o dedurre email, numeri di telefono, indirizzi di casa o altri dati \
personali di contatto. Per "pagina_collaborazioni" indica solo l'URL di una pagina pubblica \
"contatti/collabora" o di un modulo, oppure stringa vuota.
3. Non inventare: includi solo pagine che hai effettivamente trovato con la ricerca, con URL reale.
4. Non stimare età o altri dati personali: usa solo ciò che la pagina presenta di sé.

Quando hai finito, chiama UNA volta lo strumento consegna_risultati con l'elenco."""

TOOL_CONSEGNA = {
    "name": "consegna_risultati",
    "description": "Consegna l'elenco finale delle pagine trovate. Da chiamare una sola volta, a ricerca conclusa.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["pagine"],
        "properties": {
            "pagine": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "nome", "url", "piattaforma", "categoria", "tipo_pagina",
                        "opportunita", "motivo", "pagina_collaborazioni",
                    ],
                    "properties": {
                        "nome": {"type": "string", "description": "Nome della pagina o del brand"},
                        "url": {"type": "string"},
                        "piattaforma": {"type": "string", "description": "Sito web, Instagram, TikTok, YouTube, LinkedIn, Substack, Discord, ..."},
                        "categoria": {"type": "string", "description": "Es. social media manager, web developer, content creator"},
                        "tipo_pagina": {"type": "string", "enum": ["professionista", "creator", "community", "evento", "newsletter_podcast"]},
                        "opportunita": {"type": "string", "enum": ["collaborazione", "community", "contenuti"]},
                        "motivo": {"type": "string", "description": "Perché è rilevante per Fisco Chiaro (max 2 frasi)"},
                        "pagina_collaborazioni": {"type": "string", "description": "URL pubblico contatti/collabora, oppure stringa vuota"},
                    },
                },
            }
        },
    },
}

TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 15,
     "user_location": {"type": "approximate", "country": "IT"}},
    TOOL_CONSEGNA,
]

# Rete di sicurezza: nessun dato di contatto personale finisce nel CSV.
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_TELEFONO = re.compile(r"(?:\+39[\s.]?)?\b3\d{2}[\s.]?\d{6,7}\b|\b0\d{1,3}[\s.]?\d{5,8}\b")


def ripulisci(testo: str) -> str:
    return RE_TELEFONO.sub("[rimosso]", RE_EMAIL.sub("[rimosso]", testo))


def esegui_ricerca(client: anthropic.Anthropic, nicchia: str, citta: str, massimo: int) -> list[dict]:
    zona = f" con base a {citta} o dintorni" if citta else " in Italia"
    richiesta = (
        f"Trova fino a {massimo} pagine pubbliche di giovani che lavorano nel digitale "
        f"nella nicchia «{nicchia}»{zona}. Varia le fonti (siti portfolio, YouTube, "
        f"Instagram/TikTok business, LinkedIn pagine aziendali, community, newsletter, eventi)."
    )
    messages = [{"role": "user", "content": richiesta}]

    for _ in range(MAX_CONTINUAZIONI):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "high"},
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Richiesta rifiutata: {response.stop_details}")

        messages.append({"role": "assistant", "content": response.content})

        consegna = next(
            (b for b in response.content if b.type == "tool_use" and b.name == "consegna_risultati"),
            None,
        )
        if consegna is not None:
            return consegna.input["pagine"]

        if response.stop_reason == "pause_turn":
            continue  # il server riprende la ricerca da dove si era fermato
        if response.stop_reason in ("end_turn", "max_tokens"):
            messages.append({
                "role": "user",
                "content": "Consegna ora i risultati con lo strumento consegna_risultati.",
            })
            continue
        raise RuntimeError(f"Stop inatteso: {response.stop_reason}")

    raise RuntimeError("L'agente non ha consegnato risultati entro il limite di continuazioni.")


def url_gia_salvati() -> set[str]:
    if not CSV_PATH.exists():
        return set()
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return {riga["url"].rstrip("/").lower() for riga in csv.DictReader(f)}


def salva(pagine: list[dict], nicchia: str) -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    gia_visti = url_gia_salvati()
    nuovo_file = not CSV_PATH.exists()
    nuove = 0
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPI)
        if nuovo_file:
            writer.writeheader()
        for p in pagine:
            chiave = p["url"].rstrip("/").lower()
            if not chiave.startswith("http") or chiave in gia_visti:
                continue
            gia_visti.add(chiave)
            riga = {k: ripulisci(str(p.get(k, ""))) for k in CAMPI if k in p}
            riga["nicchia_ricerca"] = nicchia
            riga["data_ricerca"] = date.today().isoformat()
            writer.writerow(riga)
            nuove += 1
    return nuove


def main() -> None:
    parser = argparse.ArgumentParser(description="Mappa pagine pubbliche di giovani del digitale per Fisco Chiaro.")
    parser.add_argument("--nicchia", default="freelance digitali (social media manager, web designer, content creator)")
    parser.add_argument("--citta", default="")
    parser.add_argument("--max", type=int, default=20, help="Numero massimo di pagine per ricerca")
    args = parser.parse_args()

    client = anthropic.Anthropic()
    try:
        pagine = esegui_ricerca(client, args.nicchia, args.citta, args.max)
    except anthropic.AuthenticationError:
        sys.exit("Chiave API non valida: imposta ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        sys.exit("Limite di richieste raggiunto: riprova tra qualche minuto.")
    except anthropic.APIStatusError as e:
        sys.exit(f"Errore API ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Errore di rete: controlla la connessione.")

    nuove = salva(pagine, args.nicchia)
    print(json.dumps(pagine, ensure_ascii=False, indent=2))
    print(f"\n{len(pagine)} pagine trovate, {nuove} nuove aggiunte a {CSV_PATH}")


if __name__ == "__main__":
    main()
