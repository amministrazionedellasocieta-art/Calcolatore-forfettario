"""Catalogo delle professioni digitali con il relativo inquadramento fiscale.

E' la parte che manca ai simulatori generalisti: partire dal lavoro reale
("faccio lo streamer", "vendo su Amazon FBA") e arrivare a codice ATECO,
coefficiente di redditivita', cassa previdenziale e adempimenti specifici.

I codici sono aggiornati alla classificazione ATECO 2025 (in vigore dal
01/04/2025). I coefficienti restano quelli dell'Allegato 4 L. 190/2014,
agganciati all'attivita' corrispondente nella vecchia classificazione.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from . import parametri

# Inquadramento previdenziale
GS = "gestione_separata"
COMMERCIANTI = "commercianti"
ARTIGIANI = "artigiani"
DIPENDE = "dipende"
NESSUNO = "nessuno"

LABEL_GESTIONE = {
    GS: "Gestione Separata INPS",
    COMMERCIANTI: "Gestione Commercianti INPS",
    ARTIGIANI: "Gestione Artigiani INPS",
    DIPENDE: "Da valutare (professionale o d'impresa)",
    NESSUNO: "Nessun obbligo contributivo da attivita'",
}


@dataclass(frozen=True)
class Professione:
    """Una professione digitale e il suo inquadramento."""

    slug: str
    nome: str
    categoria: str
    ateco: str
    ateco_descrizione: str
    gruppo_coefficiente: str
    natura: str            # "professionale", "impresa", "dipende"
    gestione_inps: str
    camera_commercio: bool
    piattaforme: tuple[str, ...] = ()
    alias: tuple[str, ...] = ()
    note: tuple[str, ...] = ()
    attenzione: tuple[str, ...] = ()

    @property
    def coefficiente(self) -> float:
        return parametri.COEFFICIENTI[self.gruppo_coefficiente][0]

    @property
    def coefficiente_pct(self) -> int:
        return round(self.coefficiente * 100)

    @property
    def gestione_label(self) -> str:
        return LABEL_GESTIONE[self.gestione_inps]

    def testo_ricerca(self) -> str:
        return " ".join(
            (self.nome, self.categoria, self.ateco, self.ateco_descrizione)
            + self.alias
            + self.piattaforme
        ).lower()


def _p(**kwargs) -> Professione:
    return Professione(**kwargs)


CATALOGO: tuple[Professione, ...] = (
    # ------------------------------------------------------------------ CREATOR
    _p(
        slug="influencer",
        nome="Influencer / Creator sponsorizzato",
        categoria="Creator & Media",
        ateco="73.11.03",
        ateco_descrizione="Attivita' di influencer marketing",
        gruppo_coefficiente="professionale",
        natura="impresa",
        gestione_inps=COMMERCIANTI,
        camera_commercio=True,
        piattaforme=("Instagram", "TikTok", "YouTube", "Meta"),
        alias=("creator", "sponsorizzazioni", "adv", "brand ambassador"),
        note=(
            "Codice nato con ATECO 2025 e dedicato all'influencer marketing.",
            "I prodotti ricevuti in cambio di contenuti sono permuta: vanno "
            "fatturati al valore normale e concorrono alla soglia degli 85.000 euro.",
            "Le collaborazioni con agenzie estere seguono l'art. 7-ter: fattura "
            "senza IVA con dicitura di inversione contabile.",
        ),
        attenzione=(
            "L'attivita' svolta in forma organizzata e' reddito d'impresa: "
            "servono iscrizione al Registro Imprese e Gestione Commercianti.",
            "Obblighi AGCOM di trasparenza sui contenuti pubblicitari (#adv).",
        ),
    ),
    _p(
        slug="youtuber",
        nome="YouTuber / Video creator",
        categoria="Creator & Media",
        ateco="59.11.00",
        ateco_descrizione="Attivita' di produzione cinematografica, di video e di programmi televisivi",
        gruppo_coefficiente="altre_attivita",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("YouTube", "Google AdSense"),
        alias=("adsense", "video", "canale"),
        note=(
            "Chi vive di AdSense e produzione video usa spesso 59.11.00 (67%); "
            "chi vive di sponsorizzazioni usa 73.11.03 (78%). Con entrambe le "
            "fonti si attivano due codici, uno prevalente.",
            "AdSense fattura da Google Ireland Ltd: operazione fuori campo IVA "
            "art. 7-ter, obbligo di iscrizione al VIES.",
        ),
        attenzione=(
            "Compila il modulo fiscale USA in AdSense: senza, Google applica la "
            "ritenuta del 30% sui ricavi generati da spettatori statunitensi.",
        ),
    ),
    _p(
        slug="streamer",
        nome="Streamer (Twitch / Kick / YouTube Live)",
        categoria="Creator & Media",
        ateco="59.11.00",
        ateco_descrizione="Attivita' di produzione cinematografica, di video e di programmi televisivi",
        gruppo_coefficiente="altre_attivita",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("Twitch", "Kick", "YouTube", "StreamElements"),
        alias=("live", "gaming", "abbonamenti", "bits", "donazioni"),
        note=(
            "Subscription, bits e ad revenue sono corrispettivi di una prestazione "
            "verso la piattaforma: vanno fatturati.",
            "Le donazioni spontanee senza controprestazione sarebbero liberalita', "
            "ma quando sono legate a vantaggi (shout-out, alert, canali) sono ricavi.",
        ),
        attenzione=(
            "Verifica nel contratto quale societa' del gruppo ti paga: cambia il "
            "trattamento IVA (UE con VIES vs extra-UE).",
        ),
    ),
    _p(
        slug="onlyfans",
        nome="Creator per piattaforme in abbonamento (OnlyFans e simili)",
        categoria="Creator & Media",
        ateco="59.11.00",
        ateco_descrizione="Attivita' di produzione cinematografica, di video e di programmi televisivi",
        gruppo_coefficiente="altre_attivita",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("OnlyFans", "Patreon", "Fansly"),
        alias=("abbonamenti", "contenuti riservati", "fanpage"),
        note=(
            "Il gestore della piattaforma (per OnlyFans: Fenix International "
            "Limited, Regno Unito) e' il tuo committente: prestazione B2B "
            "extra-UE fuori campo IVA art. 7-ter.",
            "I compensi sono reddito imponibile a prescindere dall'anonimato del "
            "profilo: gli accrediti bancari sono tracciati.",
        ),
        attenzione=(
            "Regno Unito fuori dal VIES: serve comunque la comunicazione delle "
            "operazioni transfrontaliere tramite SDI.",
            "Valuta la sede legale/domicilio indicato in fattura per la privacy.",
        ),
    ),
    _p(
        slug="podcaster",
        nome="Podcaster",
        categoria="Creator & Media",
        ateco="59.20.00",
        ateco_descrizione="Attivita' di registrazione sonora e di editoria musicale",
        gruppo_coefficiente="altre_attivita",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("Spotify", "Apple Podcasts", "YouTube"),
        alias=("audio", "podcast", "radio"),
        note=(
            "Se il podcast e' monetizzato con sponsor, la componente pubblicitaria "
            "puo' ricadere in 73.11 (78%).",
        ),
    ),
    _p(
        slug="videomaker",
        nome="Videomaker / Video editor",
        categoria="Creator & Media",
        ateco="59.12.00",
        ateco_descrizione="Attivita' di post-produzione cinematografica, di video e di programmi televisivi",
        gruppo_coefficiente="altre_attivita",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("Fiverr", "Upwork", "clienti diretti"),
        alias=("montaggio", "editing", "reels", "post produzione"),
    ),
    _p(
        slug="fotografo",
        nome="Fotografo digitale / Stock",
        categoria="Creator & Media",
        ateco="74.20.00",
        ateco_descrizione="Attivita' fotografiche",
        gruppo_coefficiente="professionale",
        natura="dipende",
        gestione_inps=DIPENDE,
        camera_commercio=False,
        piattaforme=("Shutterstock", "Adobe Stock", "Getty"),
        alias=("foto", "stock", "banche immagini"),
        note=(
            "Il fotografo artistico e' lavoro autonomo; lo studio fotografico "
            "strutturato e' impresa artigiana con iscrizione in CCIAA.",
            "Le royalty da banche immagini estere seguono le regole dei diritti "
            "d'autore e vanno verificate caso per caso.",
        ),
    ),
    _p(
        slug="musicista-digitale",
        nome="Musicista / Producer digitale",
        categoria="Creator & Media",
        ateco="90.03.09",
        ateco_descrizione="Altre creazioni artistiche e letterarie",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Spotify", "DistroKid", "Bandcamp", "SIAE"),
        alias=("beat", "produzione musicale", "royalty"),
        note=(
            "I diritti d'autore percepiti come autore sono redditi di lavoro "
            "autonomo con abbattimento forfetario del 25% (40% se hai meno di 35 anni), "
            "regime diverso dal forfettario.",
        ),
    ),
    _p(
        slug="scrittore-self",
        nome="Autore self-publishing (Amazon KDP)",
        categoria="Creator & Media",
        ateco="90.03.02",
        ateco_descrizione="Attivita' di scrittori e poeti",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Amazon KDP", "Kobo", "Streetlib"),
        alias=("ebook", "kdp", "libri", "self publishing"),
        note=(
            "Le royalty KDP sono diritti d'autore: verifica se rientrano nel "
            "regime dell'art. 53 c. 2 lett. b TUIR o nell'attivita' d'impresa.",
        ),
        attenzione=("Compila il modulo fiscale USA su KDP per evitare la ritenuta del 30%.",),
    ),
    _p(
        slug="esports",
        nome="Pro player / Esports",
        categoria="Creator & Media",
        ateco="93.19.99",
        ateco_descrizione="Altre attivita' sportive",
        gruppo_coefficiente="altre_attivita",
        natura="dipende",
        gestione_inps=DIPENDE,
        camera_commercio=False,
        piattaforme=("team", "tornei", "sponsor"),
        alias=("gaming professionista", "torneo", "premi"),
        note=(
            "Gli esports non rientrano nel lavoro sportivo riformato: i compensi "
            "sono lavoro autonomo o d'impresa a seconda del contratto.",
            "I montepremi esteri possono subire ritenute alla fonte: verifica la "
            "convenzione contro le doppie imposizioni.",
        ),
    ),
    # --------------------------------------------------------------------- TECH
    _p(
        slug="sviluppatore-software",
        nome="Sviluppatore software / Programmatore",
        categoria="Tech & Dev",
        ateco="62.10.00",
        ateco_descrizione="Attivita' di programmazione informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("clienti diretti", "Upwork", "Toptal"),
        alias=("developer", "backend", "frontend", "full stack", "programmatore"),
        note=(
            "Con ATECO 2025 la programmazione informatica e' confluita in "
            "62.10.00, che comprende anche app mobili, sistemi di intelligenza "
            "artificiale e IoT.",
            "Coefficiente 67%: il gruppo 62 rientra nelle 'altre attivita''.",
        ),
    ),
    _p(
        slug="sviluppatore-app",
        nome="Sviluppatore app mobile",
        categoria="Tech & Dev",
        ateco="62.10.00",
        ateco_descrizione="Attivita' di programmazione informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("App Store", "Google Play"),
        alias=("ios", "android", "app"),
        note=(
            "Apple e Google agiscono da commissionari: la tua controparte e' la "
            "societa' irlandese del gruppo, non l'utente finale.",
            "Se vendi l'app come prodotto tuo agli utenti, l'attivita' diventa "
            "commercio elettronico diretto con obblighi OSS.",
        ),
    ),
    _p(
        slug="consulente-it",
        nome="Consulente IT / Sistemista / DevOps",
        categoria="Tech & Dev",
        ateco="62.20.00",
        ateco_descrizione="Consulenza nel settore delle tecnologie dell'informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("devops", "cloud", "sistemi", "infrastruttura"),
    ),
    _p(
        slug="cybersecurity",
        nome="Esperto cybersecurity / Penetration tester",
        categoria="Tech & Dev",
        ateco="62.20.00",
        ateco_descrizione="Consulenza nel settore delle tecnologie dell'informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("sicurezza informatica", "pentest", "ethical hacking", "bug bounty"),
        note=(
            "I premi da programmi di bug bounty esteri sono compensi di lavoro "
            "autonomo e vanno fatturati alla piattaforma che li eroga.",
        ),
    ),
    _p(
        slug="data-analyst",
        nome="Data analyst / Data scientist",
        categoria="Tech & Dev",
        ateco="62.10.00",
        ateco_descrizione="Attivita' di programmazione informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("dati", "machine learning", "bi", "analytics"),
        note=(
            "Se l'attivita' e' prevalentemente consulenziale e non di sviluppo, "
            "valuta 70.22 (consulenza gestionale) con coefficiente 78%.",
        ),
    ),
    _p(
        slug="consulente-ai",
        nome="Consulente AI / Prompt engineer",
        categoria="Tech & Dev",
        ateco="62.10.00",
        ateco_descrizione="Attivita' di programmazione informatica (incl. sistemi di IA)",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("intelligenza artificiale", "llm", "automazione ai", "prompt"),
        note=(
            "ATECO 2025 include esplicitamente i sistemi di intelligenza "
            "artificiale nella programmazione informatica.",
            "Gli abbonamenti alle API dei fornitori esteri sono acquisti di servizi "
            "in reverse charge: da forfettario paghi tu l'IVA con F24.",
        ),
    ),
    _p(
        slug="blockchain-dev",
        nome="Sviluppatore blockchain / Web3",
        categoria="Tech & Dev",
        ateco="62.10.00",
        ateco_descrizione="Attivita' di programmazione informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("smart contract", "solidity", "web3", "dapp"),
        note=(
            "I compensi incassati in cripto vanno fatturati convertendo in euro "
            "al cambio del giorno dell'operazione.",
            "Le cripto detenute vanno monitorate nel quadro dichiarativo dedicato.",
        ),
    ),
    _p(
        slug="no-code",
        nome="No-code / Automation specialist",
        categoria="Tech & Dev",
        ateco="62.20.00",
        ateco_descrizione="Consulenza nel settore delle tecnologie dell'informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Make", "Zapier", "Airtable", "n8n"),
        alias=("automazioni", "workflow", "integrazioni"),
    ),
    _p(
        slug="game-dev",
        nome="Game developer indie",
        categoria="Tech & Dev",
        ateco="62.10.00",
        ateco_descrizione="Attivita' di programmazione informatica",
        gruppo_coefficiente="altre_attivita",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Steam", "itch.io", "Epic Games"),
        alias=("videogiochi", "unity", "unreal"),
        note=("Steam (Valve) opera come rivenditore: la controparte e' la piattaforma.",),
    ),
    # ------------------------------------------------------------------- DESIGN
    _p(
        slug="web-designer",
        nome="Web designer / UX-UI designer",
        categoria="Design & Creativita'",
        ateco="74.12.01",
        ateco_descrizione="Attivita' di progettazione grafica di pagine web",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("ux", "ui", "figma", "interfacce", "siti web"),
        note=(
            "ATECO 2025 ha sostituito il vecchio 74.10.21 con 74.12.01.",
            "Se realizzi anche lo sviluppo del sito, valuta l'abbinamento con "
            "62.10.00 (coefficiente 67%).",
        ),
    ),
    _p(
        slug="graphic-designer",
        nome="Graphic designer / Brand identity",
        categoria="Design & Creativita'",
        ateco="74.12.09",
        ateco_descrizione="Altre attivita' di progettazione grafica e di comunicazione visiva",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("logo", "grafica", "illustrazione", "brand"),
        note=("Sostituisce il precedente 74.10.29 della classificazione 2007.",),
    ),
    _p(
        slug="motion-designer",
        nome="Motion designer / 3D artist",
        categoria="Design & Creativita'",
        ateco="74.12.09",
        ateco_descrizione="Altre attivita' di progettazione grafica e di comunicazione visiva",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("animazione", "3d", "blender", "after effects"),
    ),
    _p(
        slug="nft-artist",
        nome="Artista digitale / NFT",
        categoria="Design & Creativita'",
        ateco="90.03.09",
        ateco_descrizione="Altre creazioni artistiche e letterarie",
        gruppo_coefficiente="altre_attivita",
        natura="dipende",
        gestione_inps=DIPENDE,
        camera_commercio=False,
        piattaforme=("OpenSea", "Foundation"),
        alias=("nft", "arte digitale", "cripto arte"),
        note=(
            "La vendita occasionale di opere proprie e' diversa dall'attivita' "
            "abituale di conio e rivendita, che e' impresa.",
            "Le royalty sulle rivendite successive vanno tracciate: sono ricavi.",
        ),
    ),
    # ---------------------------------------------------------------- MARKETING
    _p(
        slug="social-media-manager",
        nome="Social media manager",
        categoria="Marketing digitale",
        ateco="73.11.02",
        ateco_descrizione="Conduzione di campagne di marketing e altri servizi pubblicitari",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("smm", "social", "community manager", "calendario editoriale"),
    ),
    _p(
        slug="ads-manager",
        nome="Media buyer / Advertising manager",
        categoria="Marketing digitale",
        ateco="73.11.02",
        ateco_descrizione="Conduzione di campagne di marketing e altri servizi pubblicitari",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Meta Ads", "Google Ads", "TikTok Ads"),
        alias=("ads", "advertising", "campagne", "performance marketing"),
        attenzione=(
            "Se acquisti la pubblicita' con la tua partita IVA e la riaddebiti al "
            "cliente, il costo entra nel tuo giro d'affari e nella soglia: da "
            "forfettario e' un costo non deducibile. Meglio far pagare il cliente.",
        ),
    ),
    _p(
        slug="seo-specialist",
        nome="SEO specialist",
        categoria="Marketing digitale",
        ateco="73.11.02",
        ateco_descrizione="Conduzione di campagne di marketing e altri servizi pubblicitari",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("posizionamento", "search", "link building"),
    ),
    _p(
        slug="copywriter",
        nome="Copywriter / Content writer",
        categoria="Marketing digitale",
        ateco="73.11.01",
        ateco_descrizione="Ideazione di campagne pubblicitarie",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("copy", "testi", "storytelling", "ghostwriting"),
        note=(
            "Il copy pubblicitario sta in 73.11; la scrittura d'autore (articoli, "
            "libri) puo' rientrare in 90.03.02 con coefficiente 67%.",
        ),
    ),
    _p(
        slug="affiliate-marketer",
        nome="Affiliate marketer",
        categoria="Marketing digitale",
        ateco="73.11.02",
        ateco_descrizione="Conduzione di campagne di marketing e altri servizi pubblicitari",
        gruppo_coefficiente="professionale",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("Amazon Associates", "Awin", "ShareASale"),
        alias=("affiliazioni", "commissioni", "referral"),
        note=(
            "Se il rapporto e' di vera intermediazione nella vendita, il "
            "coefficiente puo' essere quello degli intermediari del commercio "
            "(62%): dipende dal contratto di affiliazione.",
            "Le commissioni Amazon Associates arrivano da societa' estere del "
            "gruppo: operazione fuori campo IVA art. 7-ter.",
        ),
    ),
    _p(
        slug="digital-strategist",
        nome="Digital strategist / Growth consultant",
        categoria="Marketing digitale",
        ateco="70.22.09",
        ateco_descrizione="Altre attivita' di consulenza imprenditoriale e gestionale",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("consulenza marketing", "growth", "strategia"),
    ),
    _p(
        slug="email-marketer",
        nome="Email marketing / Funnel specialist",
        categoria="Marketing digitale",
        ateco="73.11.02",
        ateco_descrizione="Conduzione di campagne di marketing e altri servizi pubblicitari",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Mailchimp", "ActiveCampaign", "Klaviyo"),
        alias=("newsletter", "funnel", "automation marketing"),
    ),
    # --------------------------------------------------------------- E-COMMERCE
    _p(
        slug="ecommerce",
        nome="E-commerce proprio (shop online)",
        categoria="E-commerce & Vendite",
        ateco="47.91.10",
        ateco_descrizione="Commercio al dettaglio di qualsiasi tipo di prodotto effettuato via internet",
        gruppo_coefficiente="commercio",
        natura="impresa",
        gestione_inps=COMMERCIANTI,
        camera_commercio=True,
        piattaforme=("Shopify", "WooCommerce", "PrestaShop"),
        alias=("shop online", "negozio online", "vendita online"),
        note=(
            "Coefficiente 40%: il piu' favorevole tra quelli del digitale.",
            "Serve la SCIA al SUAP del Comune oltre all'iscrizione al Registro Imprese.",
            "Vendite B2C verso altri Paesi UE: sopra 10.000 euro annui complessivi "
            "scatta l'IVA del Paese del cliente, con registrazione OSS.",
        ),
        attenzione=(
            "Il forfettario non puo' aderire all'OSS applicando l'imposta "
            "sostitutiva sulle vendite estere senza valutare gli effetti: "
            "verifica la posizione con un professionista prima di superare la soglia.",
        ),
    ),
    _p(
        slug="dropshipping",
        nome="Dropshipping",
        categoria="E-commerce & Vendite",
        ateco="47.91.10",
        ateco_descrizione="Commercio al dettaglio di qualsiasi tipo di prodotto effettuato via internet",
        gruppo_coefficiente="commercio",
        natura="impresa",
        gestione_inps=COMMERCIANTI,
        camera_commercio=True,
        piattaforme=("Shopify", "AliExpress", "CJ Dropshipping"),
        alias=("dropship", "fornitore diretto"),
        note=(
            "Attenzione a distinguere se vendi in nome proprio (sei tu il "
            "venditore, ricavo pieno) o come intermediario (ricavo = provvigione).",
            "Con merce spedita da fuori UE l'importazione e i dazi ricadono sul "
            "cliente finale se non gestisci tu lo sdoganamento: e' la causa numero "
            "uno di contestazioni.",
        ),
        attenzione=(
            "Nel forfettario il costo della merce non e' deducibile: con margini "
            "bassi il coefficiente del 40% puo' penalizzarti rispetto all'ordinario.",
        ),
    ),
    _p(
        slug="amazon-fba",
        nome="Venditore Amazon FBA / marketplace",
        categoria="E-commerce & Vendite",
        ateco="47.91.10",
        ateco_descrizione="Commercio al dettaglio di qualsiasi tipo di prodotto effettuato via internet",
        gruppo_coefficiente="commercio",
        natura="impresa",
        gestione_inps=COMMERCIANTI,
        camera_commercio=True,
        piattaforme=("Amazon", "eBay", "Zalando"),
        alias=("fba", "marketplace", "vendo su amazon"),
        note=(
            "Le fee Amazon sono acquisti di servizi da societa' lussemburghese: "
            "reverse charge con integrazione elettronica.",
        ),
        attenzione=(
            "Se la merce viene stoccata in magazzini esteri (programmi paneuropei) "
            "serve l'identificazione IVA nel Paese del magazzino: l'OSS non copre "
            "questi trasferimenti. E' incompatibile con la semplicita' del forfettario.",
        ),
    ),
    _p(
        slug="print-on-demand",
        nome="Print on demand",
        categoria="E-commerce & Vendite",
        ateco="47.91.10",
        ateco_descrizione="Commercio al dettaglio di qualsiasi tipo di prodotto effettuato via internet",
        gruppo_coefficiente="commercio",
        natura="impresa",
        gestione_inps=COMMERCIANTI,
        camera_commercio=True,
        piattaforme=("Printful", "Printify", "Redbubble"),
        alias=("pod", "magliette", "merch"),
        note=(
            "Su Redbubble e simili spesso non vendi tu: incassi una royalty sul "
            "design, con inquadramento diverso dalla vendita diretta.",
        ),
    ),
    _p(
        slug="infoprodotti",
        nome="Infoprodotti / Corsi digitali automatizzati",
        categoria="E-commerce & Vendite",
        ateco="58.29.00",
        ateco_descrizione="Edizione di altri software",
        gruppo_coefficiente="altre_attivita",
        natura="impresa",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        piattaforme=("Gumroad", "Hotmart", "Kajabi", "Teachable"),
        alias=("corso online", "ebook", "membership", "prodotti digitali"),
        note=(
            "Sono servizi prestati tramite mezzi elettronici: la vendita B2C "
            "estera segue l'IVA del Paese del cliente sopra la soglia di 10.000 euro.",
            "Un corso registrato e automatizzato e' un prodotto digitale; un corso "
            "erogato in diretta e' una prestazione didattica: regole IVA diverse.",
        ),
    ),
    # ------------------------------------------------------- FORMAZIONE/SERVIZI
    _p(
        slug="formatore-online",
        nome="Formatore / Docente online",
        categoria="Formazione & Consulenza",
        ateco="85.59.09",
        ateco_descrizione="Altri servizi di istruzione non classificati altrove",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Zoom", "Udemy", "scuole"),
        alias=("docenza", "corsi", "formazione", "lezioni"),
        note=(
            "Le prestazioni didattiche possono essere esenti IVA (art. 10 DPR "
            "633/72) se rese da scuole riconosciute: da forfettario il tema non "
            "si pone, ma cambia in caso di uscita dal regime.",
        ),
    ),
    _p(
        slug="tutor-online",
        nome="Tutor / Insegnante privato online",
        categoria="Formazione & Consulenza",
        ateco="85.59.20",
        ateco_descrizione="Corsi di formazione e corsi di aggiornamento professionale",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        piattaforme=("Preply", "Superprof", "italki"),
        alias=("ripetizioni", "lezioni private", "insegnante"),
        note=(
            "I docenti con lezioni private hanno un regime dedicato con imposta "
            "sostitutiva al 15% se dipendenti della scuola: valuta l'alternativa.",
        ),
    ),
    _p(
        slug="coach",
        nome="Coach / Mental coach online",
        categoria="Formazione & Consulenza",
        ateco="96.09.09",
        ateco_descrizione="Altre attivita' di servizi per la persona n.c.a.",
        gruppo_coefficiente="altre_attivita",
        natura="dipende",
        gestione_inps=DIPENDE,
        camera_commercio=False,
        alias=("coaching", "life coach", "business coach", "percorsi"),
        note=(
            "Professione non ordinistica: l'inquadramento cambia molto in base al "
            "contenuto reale (consulenza aziendale, formazione, benessere).",
        ),
        attenzione=("Attenzione al confine con le professioni sanitarie regolamentate.",),
    ),
    _p(
        slug="traduttore",
        nome="Traduttore / Interprete",
        categoria="Formazione & Consulenza",
        ateco="74.30.00",
        ateco_descrizione="Traduzione e interpretariato",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("traduzioni", "localizzazione", "sottotitoli"),
    ),
    _p(
        slug="virtual-assistant",
        nome="Virtual assistant",
        categoria="Formazione & Consulenza",
        ateco="82.11.01",
        ateco_descrizione="Servizi integrati di supporto per le funzioni d'ufficio",
        gruppo_coefficiente="altre_attivita",
        natura="dipende",
        gestione_inps=DIPENDE,
        camera_commercio=True,
        alias=("assistente virtuale", "segretaria online", "back office"),
    ),
    _p(
        slug="recruiter",
        nome="Recruiter / Consulente HR freelance",
        categoria="Formazione & Consulenza",
        ateco="70.22.09",
        ateco_descrizione="Altre attivita' di consulenza imprenditoriale e gestionale",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("hr", "selezione", "talent"),
        attenzione=(
            "L'attivita' di intermediazione fra domanda e offerta di lavoro e' "
            "riservata ai soggetti autorizzati dal Ministero: la consulenza HR e' "
            "un'altra cosa.",
        ),
    ),
    _p(
        slug="project-manager",
        nome="Project manager freelance",
        categoria="Formazione & Consulenza",
        ateco="70.22.09",
        ateco_descrizione="Altre attivita' di consulenza imprenditoriale e gestionale",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("pm", "agile", "scrum master"),
    ),
    # ----------------------------------------------------------------- FINANZA
    _p(
        slug="trader-cripto",
        nome="Investitore / Trader in cripto-attivita'",
        categoria="Finanza & Cripto",
        ateco="",
        ateco_descrizione="Nessun codice: reddito diverso, non attivita' d'impresa",
        gruppo_coefficiente="altre_attivita",
        natura="dipende",
        gestione_inps=NESSUNO,
        camera_commercio=False,
        piattaforme=("Binance", "Coinbase", "Kraken"),
        alias=("bitcoin", "crypto", "trading", "plusvalenze"),
        note=(
            "L'investimento personale non richiede partita IVA: le plusvalenze "
            "sono redditi diversi tassati con imposta sostitutiva.",
            "Dal 2026 l'aliquota e' il 33% (26% solo per i token di moneta "
            "elettronica ancorati all'euro conformi a MiCAR) e non esiste piu' "
            "alcuna soglia di esenzione.",
            "Vanno compilati il quadro dei redditi diversi e quello del "
            "monitoraggio, con l'imposta sul valore delle cripto-attivita' del 2 per mille.",
        ),
        attenzione=(
            "Il trading sistematico per conto terzi e' tutt'altro: e' attivita' "
            "riservata e vigilata.",
        ),
    ),
    _p(
        slug="consulente-cripto",
        nome="Consulente / Divulgatore finanziario digitale",
        categoria="Finanza & Cripto",
        ateco="70.22.09",
        ateco_descrizione="Altre attivita' di consulenza imprenditoriale e gestionale",
        gruppo_coefficiente="professionale",
        natura="professionale",
        gestione_inps=GS,
        camera_commercio=False,
        alias=("divulgazione", "educazione finanziaria", "newsletter finanziaria"),
        attenzione=(
            "La consulenza finanziaria personalizzata e' riservata agli iscritti "
            "all'albo OCF: la divulgazione generica no. Il confine e' sanzionato.",
        ),
    ),
)


CATEGORIE: tuple[str, ...] = tuple(dict.fromkeys(p.categoria for p in CATALOGO))

_INDICE = {p.slug: p for p in CATALOGO}


def get(slug: str) -> Professione:
    """Restituisce la professione con lo slug indicato."""
    try:
        return _INDICE[slug]
    except KeyError as exc:  # pragma: no cover - difensivo
        raise KeyError(f"professione sconosciuta: {slug!r}") from exc


def per_categoria(categoria: str) -> tuple[Professione, ...]:
    return tuple(p for p in CATALOGO if p.categoria == categoria)


def cerca(query: str, limite: int = 10) -> tuple[Professione, ...]:
    """Ricerca testuale semplice su nome, alias, ATECO e piattaforme."""
    termini = [t for t in query.lower().split() if t]
    if not termini:
        return CATALOGO[:limite]

    risultati: list[tuple[int, Professione]] = []
    for prof in CATALOGO:
        testo = prof.testo_ricerca()
        punteggio = 0
        for termine in termini:
            if termine in prof.nome.lower():
                punteggio += 3
            elif any(termine in alias for alias in prof.alias):
                punteggio += 2
            elif termine in testo:
                punteggio += 1
        if punteggio:
            risultati.append((punteggio, prof))

    risultati.sort(key=lambda coppia: (-coppia[0], coppia[1].nome))
    return tuple(prof for _, prof in risultati[:limite])


def slugs() -> Iterable[str]:
    return _INDICE.keys()
