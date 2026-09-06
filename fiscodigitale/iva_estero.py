"""Territorialita' IVA e piattaforme digitali.

Il lavoro digitale e' quasi sempre transfrontaliero: incassi da Dublino,
compri pubblicita' in Irlanda, vendi corsi a clienti tedeschi. E' qui che si
concentrano gli errori piu' costosi, perche' il forfettario non e' esonerato
dagli obblighi sugli acquisti esteri: li paga di tasca propria.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import parametri as P

# Direzione dell'operazione
VENDITA = "vendita"
ACQUISTO = "acquisto"

# Controparte
B2B = "B2B"
B2C = "B2C"

# Area geografica
ITALIA = "IT"
UE = "UE"
EXTRA_UE = "EXTRA_UE"

# Oggetto
SERVIZIO = "servizio"
SERVIZIO_ELETTRONICO = "servizio_elettronico"  # TTE: corsi registrati, software, ebook
BENE = "bene"

FORFETTARIO = "forfettario"
ORDINARIO = "ordinario"


@dataclass(frozen=True)
class Operazione:
    direzione: str = VENDITA
    oggetto: str = SERVIZIO
    controparte: str = B2B
    area: str = UE
    regime: str = FORFETTARIO
    importo: float = 0.0
    vendite_ue_b2c_anno: float = 0.0
    acquisti_beni_ue_anno: float = 0.0


@dataclass(frozen=True)
class EsitoIva:
    titolo: str
    iva: str
    riferimento: str
    documento: str
    natura: str = ""
    dicitura: str = ""
    adempimenti: tuple[str, ...] = ()
    scadenze: tuple[str, ...] = ()
    rischi: tuple[str, ...] = ()


def _vendita(op: Operazione) -> EsitoIva:
    forfe = op.regime == FORFETTARIO

    if op.area == ITALIA:
        if forfe:
            return EsitoIva(
                titolo="Vendita in Italia (forfettario)",
                iva="Nessuna IVA in fattura",
                riferimento="art. 1 c. 58 L. 190/2014",
                documento="TD01 - fattura elettronica via SDI",
                natura="N2.2",
                dicitura="Operazione non soggetta a IVA ai sensi dell'art. 1, "
                         "commi 54-89, L. 190/2014. Regime forfettario.",
                adempimenti=(
                    "Fattura elettronica obbligatoria anche per i forfettari.",
                    f"Imposta di bollo da {P.IMPOSTA_BOLLO:.2f} euro sulle fatture "
                    f"oltre {P.SOGLIA_BOLLO:.2f} euro (assolta in modo virtuale).",
                    "Non subisci ritenuta d'acconto: inserisci la dicitura che la esclude.",
                ),
                scadenze=("Entro 12 giorni dall'effettuazione dell'operazione.",),
            )
        return EsitoIva(
            titolo="Vendita in Italia (ordinario)",
            iva=f"IVA {P.IVA_ORDINARIA * 100:.0f}% (salvo aliquote ridotte o esenzioni)",
            riferimento="DPR 633/72",
            documento="TD01 - fattura elettronica via SDI",
            adempimenti=("Liquidazione IVA mensile o trimestrale, LIPE trimestrali.",),
            scadenze=("Versamento IVA entro il 16 del mese successivo al periodo.",),
        )

    if op.oggetto == BENE:
        if op.area == UE and op.controparte == B2B:
            if forfe:
                return EsitoIva(
                    titolo="Cessione di beni a impresa UE (forfettario)",
                    iva="Nessuna IVA, ma NON e' una cessione intracomunitaria",
                    riferimento="art. 41 c. 2-bis DL 331/93",
                    documento="TD01 con codice destinatario XXXXXXX",
                    natura="N2.2",
                    dicitura="Operazione non soggetta - regime forfettario, "
                             "non costituisce cessione intracomunitaria.",
                    adempimenti=(
                        "Nessun INTRASTAT sulle cessioni di beni.",
                        "L'operazione va comunque trasmessa via SDI.",
                    ),
                    rischi=(
                        "Il cliente estero potrebbe pretendere una cessione "
                        "intracomunitaria: spiegagli il regime, la fattura e' corretta.",
                    ),
                )
            return EsitoIva(
                titolo="Cessione intracomunitaria di beni",
                iva="Non imponibile",
                riferimento="art. 41 DL 331/93",
                documento="TD01",
                natura="N3.2",
                dicitura="Operazione non imponibile ai sensi dell'art. 41 DL 331/93.",
                adempimenti=(
                    "Iscrizione al VIES e verifica della partita IVA del cliente.",
                    "Elenchi INTRASTAT delle cessioni.",
                    "Conserva la prova del trasporto in altro Stato UE.",
                ),
            )
        if op.area == UE and op.controparte == B2C:
            sopra_soglia = op.vendite_ue_b2c_anno + op.importo > P.SOGLIA_OSS
            if sopra_soglia:
                return EsitoIva(
                    titolo="Vendita a distanza a privato UE oltre soglia",
                    iva="IVA del Paese del cliente",
                    riferimento="art. 38-bis DL 331/93; regime OSS",
                    documento="Registrazione OSS e dichiarazione trimestrale",
                    adempimenti=(
                        f"Superata la soglia unica di {P.SOGLIA_OSS:,.0f} euro annui: "
                        "registrati all'OSS o apri una posizione IVA in ogni Paese.",
                        "Applica l'aliquota del Paese di destinazione.",
                    ),
                    rischi=(
                        "Per un forfettario l'adesione all'OSS e' un passaggio "
                        "delicato: fatti assistere prima di superare la soglia.",
                    ),
                )
            return EsitoIva(
                titolo="Vendita a distanza a privato UE sotto soglia",
                iva="Regime italiano (nessuna IVA se forfettario)" if forfe
                    else f"IVA italiana {P.IVA_ORDINARIA * 100:.0f}%",
                riferimento="art. 41 c. 1 lett. b DL 331/93",
                documento="TD01 o corrispettivo",
                adempimenti=(
                    f"Monitora il cumulo annuo: la soglia unica UE e' "
                    f"{P.SOGLIA_OSS:,.0f} euro (attualmente a "
                    f"{op.vendite_ue_b2c_anno:,.0f} euro).",
                ),
            )
        return EsitoIva(
            titolo="Esportazione di beni fuori UE",
            iva="Non imponibile" if not forfe else "Nessuna IVA (regime forfettario)",
            riferimento="art. 8 DPR 633/72",
            documento="TD01 + bolletta doganale",
            natura="N3.1",
            adempimenti=("Conserva il messaggio di uscita della dogana come prova.",),
        )

    # Servizi
    if op.controparte == B2B:
        return EsitoIva(
            titolo=f"Servizio a impresa {'UE' if op.area == UE else 'extra-UE'}",
            iva="Fuori campo IVA in Italia: l'imposta e' dovuta dal committente",
            riferimento="art. 7-ter DPR 633/72",
            documento="TD01 con codice destinatario XXXXXXX",
            natura="N2.1",
            dicitura=(
                "Inversione contabile - reverse charge, art. 7-ter DPR 633/72"
                if op.area == UE
                else "Operazione non soggetta ad IVA, art. 7-ter DPR 633/72"
            ),
            adempimenti=(
                (
                    "Iscrizione al VIES obbligatoria prima della prima operazione.",
                    "Verifica la partita IVA del cliente nella banca dati VIES e "
                    "conserva la stampa.",
                    "Elenchi INTRASTAT per i servizi resi.",
                )
                if op.area == UE
                else (
                    "Nessun VIES ne' INTRASTAT verso i Paesi extra-UE.",
                    "Conserva un documento che provi lo status di soggetto passivo "
                    "del cliente (certificato, visura, contratto).",
                )
            )
            + ("L'operazione va trasmessa via SDI: assolve la comunicazione transfrontaliera.",),
            rischi=(
                "Senza iscrizione al VIES l'operazione e' irregolare e il cliente "
                "puo' rifiutare la fattura.",
            ) if op.area == UE else (),
        )

    # Servizi B2C
    if op.oggetto == SERVIZIO_ELETTRONICO:
        sopra_soglia = op.vendite_ue_b2c_anno + op.importo > P.SOGLIA_OSS
        if op.area == UE and sopra_soglia:
            return EsitoIva(
                titolo="Servizio elettronico a privato UE oltre soglia",
                iva="IVA del Paese del cliente",
                riferimento="art. 7-octies DPR 633/72; regime OSS",
                documento="Dichiarazione OSS trimestrale",
                adempimenti=(
                    "Registrazione al regime OSS.",
                    "Raccogli e conserva due prove non contraddittorie della "
                    "residenza del cliente (IP, dati di pagamento, indirizzo).",
                ),
                rischi=(
                    "Corsi registrati, ebook, software e abbonamenti venduti a "
                    "privati UE fanno cumulo verso la soglia di 10.000 euro.",
                ),
            )
        if op.area == UE:
            return EsitoIva(
                titolo="Servizio elettronico a privato UE sotto soglia",
                iva="Regime italiano (nessuna IVA se forfettario)" if forfe
                    else f"IVA italiana {P.IVA_ORDINARIA * 100:.0f}%",
                riferimento="art. 7-octies DPR 633/72",
                documento="TD01 o corrispettivo",
                adempimenti=(
                    f"Cumulo attuale {op.vendite_ue_b2c_anno:,.0f} euro su "
                    f"{P.SOGLIA_OSS:,.0f}: oltre la soglia cambia tutto.",
                ),
            )
        return EsitoIva(
            titolo="Servizio elettronico a privato extra-UE",
            iva="Fuori campo IVA in Italia",
            riferimento="art. 7-septies DPR 633/72",
            documento="TD01",
            natura="N2.1",
            adempimenti=("Verifica eventuali obblighi di registrazione nel Paese del cliente.",),
        )

    return EsitoIva(
        titolo=f"Servizio generico a privato {'UE' if op.area == UE else 'extra-UE'}",
        iva="Rilevante in Italia (nessuna IVA se forfettario)" if forfe
            else f"IVA italiana {P.IVA_ORDINARIA * 100:.0f}%",
        riferimento="art. 7-ter c. 1 lett. b DPR 633/72",
        documento="TD01",
        adempimenti=(
            "Verso privati vale il criterio del prestatore: si applica il regime italiano.",
        ),
    )


def _acquisto(op: Operazione) -> EsitoIva:
    forfe = op.regime == FORFETTARIO

    if op.area == ITALIA:
        return EsitoIva(
            titolo="Acquisto da fornitore italiano",
            iva="IVA esposta dal fornitore",
            riferimento="DPR 633/72",
            documento="Fattura ricevuta via SDI",
            adempimenti=(
                "Nel forfettario l'IVA sugli acquisti non e' detraibile: e' un costo."
                if forfe
                else "IVA detraibile secondo le regole ordinarie.",
            ),
        )

    if op.oggetto == BENE and op.area == UE and forfe:
        cumulo = op.acquisti_beni_ue_anno + op.importo
        if cumulo <= P.SOGLIA_OSS:
            return EsitoIva(
                titolo="Acquisto di beni UE sotto soglia (forfettario)",
                iva="Paghi l'IVA del Paese del fornitore",
                riferimento="art. 38 c. 5 lett. c DL 331/93",
                documento="Fattura estera, nessuna integrazione",
                adempimenti=(
                    f"Finche' resti sotto {P.SOGLIA_OSS:,.0f} euro annui di acquisti "
                    f"intracomunitari di beni (ora a {op.acquisti_beni_ue_anno:,.0f}) "
                    "l'acquisto e' trattato come interno al Paese del fornitore.",
                ),
                rischi=(
                    "Superata la soglia scatta l'obbligo di iscrizione al VIES e di "
                    "versamento dell'IVA italiana: il cumulo va monitorato.",
                ),
            )

    if op.oggetto == BENE:
        documento = P.CODICI_DOCUMENTO["TD18"] if op.area == UE else P.CODICI_DOCUMENTO["TD19"]
        codice = "TD18" if op.area == UE else "TD19"
        return EsitoIva(
            titolo=f"Acquisto di beni {'intracomunitario' if op.area == UE else 'da fornitore extra-UE'}",
            iva="IVA italiana da assolvere con inversione contabile"
                if op.area == UE else "IVA assolta in dogana all'importazione",
            riferimento="art. 38 DL 331/93" if op.area == UE else "art. 67 DPR 633/72",
            documento=f"{codice} - {documento}" if op.area == UE else "Bolletta doganale",
            adempimenti=(
                (
                    "Iscrizione al VIES.",
                    f"Integrazione elettronica entro il {P.GIORNO_AUTOFATTURA_ACQUISTI} "
                    "del mese successivo.",
                )
                + (
                    (
                        "Da forfettario versi l'IVA con F24 entro il "
                        f"{P.GIORNO_VERSAMENTO_IVA_REVERSE} del mese successivo, "
                        "senza poterla detrarre: e' un costo puro.",
                    )
                    if forfe
                    else ("IVA a debito e a credito nella stessa liquidazione: effetto neutro.",)
                )
                if op.area == UE
                else ("L'IVA all'importazione non e' detraibile per il forfettario.",)
            ),
        )

    # Servizi acquistati dall'estero: sempre reverse charge.
    return EsitoIva(
        titolo=f"Acquisto di servizi da fornitore {'UE' if op.area == UE else 'extra-UE'}",
        iva="IVA italiana dovuta da te con inversione contabile",
        riferimento="art. 17 c. 2 DPR 633/72",
        documento=f"TD17 - {P.CODICI_DOCUMENTO['TD17']}",
        adempimenti=(
            (
                "Iscrizione al VIES se il fornitore e' UE.",
                f"Trasmetti il TD17 via SDI entro il {P.GIORNO_AUTOFATTURA_ACQUISTI} "
                "del mese successivo al ricevimento.",
            )
            + (
                (
                    f"Versa l'IVA con F24 entro il {P.GIORNO_VERSAMENTO_IVA_REVERSE} "
                    "del mese successivo (codice tributo del mese di riferimento): "
                    "nel forfettario e' un costo secco.",
                    f"Su 100 euro di pubblicita' o software esteri paghi "
                    f"{P.IVA_ORDINARIA * 100:.0f} euro di IVA in piu'.",
                )
                if forfe
                else ("Doppia annotazione nei registri: l'operazione e' neutra.",)
            )
        ),
        rischi=(
            "E' l'adempimento piu' dimenticato dai forfettari: abbonamenti, "
            "pubblicita' e software esteri generano IVA da versare ogni mese.",
        ),
    )


def analizza(operazione: Operazione) -> EsitoIva:
    """Determina il trattamento IVA di una singola operazione."""
    if operazione.direzione == VENDITA:
        return _vendita(operazione)
    if operazione.direzione == ACQUISTO:
        return _acquisto(operazione)
    raise ValueError(f"direzione non valida: {operazione.direzione!r}")


# ---------------------------------------------------------------------------
# PIATTAFORME
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Piattaforma:
    slug: str
    nome: str
    societa: str
    area: str
    ruolo: str          # "committente" (ti paga), "fornitore" (ti addebita), "entrambi"
    oggetto: str
    categoria: str
    note: tuple[str, ...] = ()

    @property
    def area_label(self) -> str:
        return {ITALIA: "Italia", UE: "Unione Europea", EXTRA_UE: "Extra-UE"}[self.area]


PIATTAFORME: tuple[Piattaforma, ...] = (
    Piattaforma("youtube", "YouTube / AdSense", "Google Ireland Limited", UE, "committente",
                SERVIZIO, "Creator",
                ("Ti paga una societa' irlandese: emetti fattura senza IVA art. 7-ter "
                 "con iscrizione al VIES.",
                 "Compila il modulo fiscale USA nel pannello AdSense: senza, viene "
                 "applicata una ritenuta del 30% sui ricavi da spettatori statunitensi.")),
    Piattaforma("meta", "Meta / Facebook / Instagram", "Meta Platforms Ireland Limited", UE,
                "entrambi", SERVIZIO, "Creator",
                ("Come inserzionista ricevi fatture senza IVA: devi integrarle e "
                 "versare l'IVA italiana.",
                 "Come creator monetizzato sei tu a fatturare alla societa' irlandese.")),
    Piattaforma("tiktok", "TikTok", "TikTok Information Technologies UK / TikTok Ireland", UE,
                "entrambi", SERVIZIO, "Creator",
                ("Verifica sul contratto quale entita' ti paga: cambia l'area di riferimento.",)),
    Piattaforma("twitch", "Twitch", "Twitch Interactive (gruppo Amazon)", EXTRA_UE, "committente",
                SERVIZIO, "Creator",
                ("Le condizioni cambiano nel tempo: controlla nel pannello creator "
                 "quale societa' emette i pagamenti prima di impostare la fattura.",
                 "Sub, bits e ad revenue sono corrispettivi da fatturare.")),
    Piattaforma("onlyfans", "OnlyFans", "Fenix International Limited (Regno Unito)", EXTRA_UE,
                "committente", SERVIZIO, "Creator",
                ("Committente extra-UE dopo la Brexit: fattura fuori campo IVA art. 7-ter.",
                 "La piattaforma trattiene la propria commissione: fatturi il lordo e "
                 "la commissione e' un costo (non deducibile nel forfettario).")),
    Piattaforma("patreon", "Patreon", "Patreon (entita' variabile per area)", EXTRA_UE,
                "committente", SERVIZIO, "Creator",
                ("Verifica se incassi dai sostenitori (B2C) o dalla piattaforma: "
                 "cambia il trattamento IVA.",)),
    Piattaforma("amazon-kdp", "Amazon KDP", "Amazon Media EU S.a r.l. (Lussemburgo)", UE,
                "committente", SERVIZIO, "Creator",
                ("Royalty da societa' lussemburghese: fattura art. 7-ter con VIES.",
                 "Compila il modulo fiscale USA per evitare la ritenuta del 30%.")),
    Piattaforma("spotify", "Spotify / distributori musicali", "Entita' variabile", UE,
                "committente", SERVIZIO, "Creator",
                ("Spesso incassi tramite un distributore (DistroKid, TuneCore): il tuo "
                 "committente e' il distributore, non Spotify.",)),
    Piattaforma("amazon-seller", "Amazon Seller / FBA", "Amazon Services Europe S.a r.l.", UE,
                "fornitore", SERVIZIO, "E-commerce",
                ("Le commissioni di vendita sono servizi in reverse charge: da "
                 "forfettario versi il 22% di IVA su ogni fattura di fee.",
                 "Se aderisci ai programmi paneuropei la merce si sposta tra magazzini "
                 "esteri: serve l'identificazione IVA nei Paesi coinvolti.")),
    Piattaforma("etsy", "Etsy", "Etsy Ireland UC", UE, "fornitore", SERVIZIO, "E-commerce",
                ("Le fee Etsy sono in reverse charge.",
                 "Attenzione a chi risulta venditore verso il cliente finale.")),
    Piattaforma("shopify", "Shopify", "Shopify International Limited (Irlanda)", UE, "fornitore",
                SERVIZIO, "E-commerce",
                ("L'abbonamento e' un servizio UE in reverse charge: integrazione e "
                 "versamento IVA ogni mese.",)),
    Piattaforma("stripe", "Stripe", "Stripe Payments Europe Limited (Irlanda)", UE, "fornitore",
                SERVIZIO, "Pagamenti",
                ("Le commissioni sono esenti o fuori campo a seconda del servizio: "
                 "verifica il documento ricevuto prima di integrarlo.",
                 "Fatturi l'importo lordo al cliente, non il netto accreditato da Stripe.")),
    Piattaforma("paypal", "PayPal", "PayPal (Europe) S.a r.l. (Lussemburgo)", UE, "fornitore",
                SERVIZIO, "Pagamenti",
                ("Come per Stripe: il ricavo e' il lordo pagato dal cliente.",)),
    Piattaforma("apple", "App Store", "Apple Distribution International (Irlanda)", UE,
                "committente", SERVIZIO, "Tech",
                ("Apple opera come commissionario: la tua controparte e' la societa' "
                 "irlandese, non l'utente finale.",)),
    Piattaforma("google-play", "Google Play", "Google Commerce Limited (Irlanda)", UE,
                "committente", SERVIZIO, "Tech",
                ("Stesso schema dell'App Store.",)),
    Piattaforma("steam", "Steam", "Valve Corporation", EXTRA_UE, "committente", SERVIZIO, "Tech",
                ("Valve agisce da rivenditore verso i giocatori: tu fatturi a Valve.",)),
    Piattaforma("upwork", "Upwork", "Upwork Global Inc. (USA)", EXTRA_UE, "entrambi", SERVIZIO,
                "Freelance",
                ("Distingui il cliente finale dalla piattaforma: spesso il committente "
                 "e' il cliente e la piattaforma ti addebita solo una fee.",)),
    Piattaforma("fiverr", "Fiverr", "Fiverr International Ltd.", EXTRA_UE, "entrambi", SERVIZIO,
                "Freelance",
                ("La commissione trattenuta e' un costo: fatturi comunque il lordo.",)),
    Piattaforma("udemy", "Udemy", "Udemy (entita' variabile)", EXTRA_UE, "committente",
                SERVIZIO_ELETTRONICO, "Formazione",
                ("Se la piattaforma vende il corso agli utenti, il tuo ricavo e' una "
                 "royalty dalla piattaforma, non una vendita ai corsisti.",)),
    Piattaforma("gumroad", "Gumroad / Hotmart / Kajabi", "Entita' variabile", EXTRA_UE,
                "entrambi", SERVIZIO_ELETTRONICO, "Formazione",
                ("Verifica se la piattaforma agisce da 'merchant of record' (vende lei) "
                 "o da semplice incassatore per tuo conto: cambia chi deve l'IVA.",)),
    Piattaforma("openai", "Fornitori AI e SaaS esteri", "Entita' UE o USA", UE, "fornitore",
                SERVIZIO, "Tech",
                ("Abbonamenti API e software: reverse charge mensile.",
                 "Comunica la partita IVA al fornitore per non farti addebitare l'IVA estera.")),
    Piattaforma("google-ads", "Google Ads", "Google Ireland Limited", UE, "fornitore", SERVIZIO,
                "Marketing",
                ("Ogni euro di advertising genera 22 centesimi di IVA da versare se sei "
                 "forfettario.",)),
)

_INDICE_PIATTAFORME = {p.slug: p for p in PIATTAFORME}


def piattaforma(slug: str) -> Piattaforma:
    return _INDICE_PIATTAFORME[slug]


def analizza_piattaforma(
    slug: str,
    *,
    regime: str = FORFETTARIO,
    direzione: str | None = None,
    importo: float = 0.0,
) -> tuple[Piattaforma, EsitoIva]:
    """Trattamento IVA delle operazioni con una piattaforma nota."""
    p = piattaforma(slug)
    if direzione is None:
        direzione = ACQUISTO if p.ruolo == "fornitore" else VENDITA

    operazione = Operazione(
        direzione=direzione,
        oggetto=p.oggetto,
        controparte=B2B,
        area=p.area,
        regime=regime,
        importo=importo,
    )
    return p, analizza(operazione)


def iva_reverse_charge(importo: float, aliquota: float = P.IVA_ORDINARIA) -> float:
    """IVA da versare su un acquisto estero in reverse charge."""
    return round(max(0.0, importo) * aliquota, 2)
