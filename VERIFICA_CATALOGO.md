# Verifica del catalogo ATECO e previdenziale

Verifica del 17 ottobre 2026 sulle **44 schede** del catalogo. Il catalogo precedente conteneva **15 schede con codici non presenti al livello di sottocategoria ATECO 2025**. Quattro schede di commercio online riusavano `47.91.10` con la descrizione precedente, mentre quel codice nel 2025 identifica intermediazione al dettaglio di articoli di seconda mano.

La struttura, le descrizioni dei 31 codici candidati e i raccordi sono stati confrontati con i file ISTAT. Nel 2026 ISTAT ha aggiornato i raccordi senza modificare la struttura della classificazione. Il coefficiente viene riferito al contenuto della precedente classificazione, secondo l'art. 1 D.Lgs. 81/2025; il prefisso del codice 2025 da solo non basta. Il raccordo e' uno strumento statistico: quando l'attivita' concreta e' ambigua non certifica il trattamento fiscale.

Sette schede generiche non ricevono piu' un codice automatico. Gli scenari proposti non sono esaustivi: se nessuno descrive l'attivita' occorre una classificazione personalizzata.

## Regole previdenziali applicate nell'interfaccia

- Per i servizi il mestiere non assegna automaticamente la Gestione Separata: occorre indicare la natura dell'attivita'. La forma d'impresa richiede conferma della gestione e dei requisiti effettivi; Commercianti e, per il fotografo, Artigiani sono scenari di confronto, non iscrizioni automatiche.
- Per creator e alcune prestazioni artistiche o tecniche viene richiesta verifica del possibile FPLS. Se il caso rientra o puo' rientrare nel FPLS il calcolo si interrompe: il motore non lo implementa e non lo sostituisce con la Gestione Separata. Riferimento: INPS 44/2025.
- Per attivita' professionali e d'impresa contemporanee non basta individuare quella con piu' ricavi: la verifica riguarda le singole iscrizioni. I totali del modello a gestione unica non vengono pubblicati nell'interfaccia o nella CLI. Riferimento: art. 12 c. 11 DL 78/2010 e INPS 78/2013.
- Camera di Commercio e adempimenti seguono la natura risolta, evitando di richiedere ComUnica a un professionista solo perche' la scheda originaria indicava impresa.
- Contratti di agenzia/affiliazione, diritti d'autore, NFT, HR riservato e attivita' finanziarie richiedono una verifica specifica. La conferma dell'utilizzatore non costituisce una certificazione del software.

## Esito per scheda

ATECO proposto significa scenario orientativo. Il coefficiente e' subordinato al contenuto indicato. `Da scegliere` sospende i numeri fino alla selezione; le ulteriori verifiche previdenziali possono mantenere la sospensione.

| Scheda | Codice precedente | Codice proposto o opzioni | Coefficiente degli scenari | Verifica |
| --- | --- | --- | --- | --- |
| influencer | 73.11.03 | 73.11.03 | 78% | contratti specialistici, FPLS, natura e previdenza |
| youtuber | 59.11.00 | 59.11.00 | 67% | FPLS, natura e previdenza |
| streamer | 59.11.00 | 59.11.00 | 67% | FPLS, natura e previdenza |
| onlyfans | 59.11.00 | 59.11.00 | 67% | FPLS, natura e previdenza |
| podcaster | 59.20.00 | 59.20.10 | 67% | FPLS, natura e previdenza |
| videomaker | 59.12.00 | 59.12.00 | 67% | FPLS, natura e previdenza |
| fotografo | 74.20.00 | 74.20.19 | 78% | FPLS, natura e previdenza |
| musicista-digitale | 90.03.09 | 90.11.09 | 67% | contratti specialistici, FPLS, natura e previdenza |
| scrittore-self | 90.03.02 | 58.11.00 | 67% | contratti specialistici, natura e previdenza |
| esports | 93.19.99 | 93.19.99 | 67% | contratti specialistici, natura e previdenza |
| sviluppatore-software | 62.10.00 | 62.10.00 | 67% | natura e previdenza |
| sviluppatore-app | 62.10.00 | 62.10.00 | 67% | natura e previdenza |
| consulente-it | 62.20.00 | 62.20.10 | 67% | natura e previdenza |
| cybersecurity | 62.20.00 | 62.20.10 | 67% | natura e previdenza |
| data-analyst | 62.10.00 | 62.10.00 | 67%, 78% | natura e previdenza |
| consulente-ai | 62.10.00 | 62.10.00 | 67% | natura e previdenza |
| blockchain-dev | 62.10.00 | 62.10.00 | 67% | natura e previdenza |
| no-code | 62.20.00 | 62.20.10 | 67% | natura e previdenza |
| game-dev | 62.10.00 | 62.10.00 | 67% | natura e previdenza |
| web-designer | 74.12.01 | 74.12.01 | 78% | natura e previdenza |
| graphic-designer | 74.12.09 | 74.12.09 | 78% | natura e previdenza |
| motion-designer | 74.12.09 | 74.12.09 | 67%, 78% | FPLS, natura e previdenza |
| nft-artist | 90.03.09 | 90.12.00 | 67% | contratti specialistici, natura e previdenza |
| social-media-manager | 73.11.02 | 73.11.02 | 78% | natura e previdenza |
| ads-manager | 73.11.02 | 73.11.02 | 78% | natura e previdenza |
| seo-specialist | 73.11.02 | 73.11.02 | 78% | natura e previdenza |
| copywriter | 73.11.01 | 73.11.01 | 78% | natura e previdenza |
| affiliate-marketer | 73.11.02 | 73.11.02 | 78% | contratti specialistici, natura e previdenza |
| digital-strategist | 70.22.09 | 70.20.09 | 78% | natura e previdenza |
| email-marketer | 73.11.02 | 73.11.02 | 78% | natura e previdenza |
| ecommerce | 47.91.10 | Da scegliere: 47.40.10, 47.61.00, 47.64.00, 47.71.10, 47.12.90 | 40% | contenuto/ruolo, natura e previdenza |
| dropshipping | 47.91.10 | Da scegliere: 47.40.10, 47.61.00, 47.64.00, 47.71.10, 47.12.90 | 40% | contenuto/ruolo, natura e previdenza |
| amazon-fba | 47.91.10 | Da scegliere: 47.40.10, 47.61.00, 47.64.00, 47.71.10, 47.12.90 | 40% | contenuto/ruolo, natura e previdenza |
| print-on-demand | 47.91.10 | Da scegliere: 47.71.10, 74.12.09 | 40%, 78% | contenuto/ruolo, natura e previdenza |
| infoprodotti | 58.29.00 | Da scegliere: 85.59.20, 58.11.00, 58.19.00, 58.29.00 | 67%, 78% | contenuto/ruolo, natura e previdenza |
| formatore-online | 85.59.09 | 85.59.20 | 78% | natura e previdenza |
| tutor-online | 85.59.20 | 85.59.99 | 78% | natura e previdenza |
| coach | 96.09.09 | Da scegliere: 70.20.09, 85.59.99 | 78% | contenuto/ruolo, natura e previdenza |
| traduttore | 74.30.00 | 74.30.00 | 78% | natura e previdenza |
| virtual-assistant | 82.11.01 | 82.10.00 | 67% | natura e previdenza |
| recruiter | 70.22.09 | 70.20.09 | 78% | contratti specialistici, natura e previdenza |
| project-manager | 70.22.09 | 70.20.09 | 78% | natura e previdenza |
| trader-cripto | — | Fuori partita IVA | Non applicabile | redditi diversi |
| consulente-cripto | 70.22.09 | Da scegliere: 85.59.20, 58.19.00 | 67%, 78% | contenuto/ruolo, contratti specialistici, natura e previdenza |

## Fonti e dati riproducibili

Il file `fiscodigitale/catalogo_verifiche.json` riporta fonti, hash SHA-256 dei tre file ISTAT consultati, codici precedenti dello scenario e criteri per ogni scheda. Non viene scaricata alcuna fonte durante l'esecuzione dell'app.

- [ISTAT, classificazione e aggiornamento 2026](https://www.istat.it/classificazione/ateco-2025/)
- [Struttura ufficiale](https://www.istat.it/wp-content/uploads/2025/02/StrutturaATECO-2025-IT-EN-DE.xlsx)
- [Note esplicative](https://www.istat.it/wp-content/uploads/2025/03/Note-esplicative-ATECO-2025-italiano-inglese.xlsx)
- [Raccordo aggiornato nel luglio 2026](https://www.istat.it/wp-content/uploads/2026/07/Aggiornamento-2026-Tavola-raccordo-bidirezionale-ATECO-2025-ATECO-2022-italiano.xlsx)
- [D.Lgs. 81/2025, art. 1](https://www.normattiva.it/eli/id/2025/06/12/25G00090/CONSOLIDATED/20260330)
- [INPS 44/2025](https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2025/02/Circolare_14835/Allegati/15927_Circolare-numero-44-del-19-02-2025.pdf)
- [INPS 78/2013, doppia iscrizione](https://servizi2.inps.it/servizi/Bussola/VisualizzaDoc.aspx?sVirtualURL=%2Fcircolari%2FCircolare+numero+78+del+14-05-2013.htm)

## Uso della libreria e della CLI

`Diagnosi.stima_utilizzabile` deve essere verificato prima di mostrare netto, confronto o piano: gli altri campi numerici restano disponibili come scenari interni per compatibilita' con i motori. Non pubblicarli come risultati applicabili se il flag e' falso. App e CLI applicano questo controllo.

Esempi:

```python
Profilo('ecommerce', 40000, codice_ateco='47.71.10')
Profilo('copywriter', 30000, natura_attivita='professionale')
Profilo('influencer', 30000, natura_attivita='professionale',
        prestazioni_spettacolo=False, verifica_specialistica_confermata=True)
```

```bash
python3 -m fiscodigitale --professione ecommerce --ricavi 40000 --ateco 47.71.10
python3 -m fiscodigitale --professione copywriter --ricavi 30000 --natura professionale
```

Se la verifica e' incompleta la CLI termina con codice 2 senza riportare numeri economici. Per casi artistici esclusi dal FPLS utilizzare `--escludi-fpls` solo dopo aver verificato le mansioni; `--verifica-specialistica-confermata` registra una verifica realmente compiuta.

## Limiti residui

Questa revisione verifica il catalogo e i suoi percorsi. Non valida tutte le altre regole del motore fiscale: restano fra l'altro le scadenze effettive annuali, i criteri di riparto degli acconti, la scadenza delle agevolazioni INPS e le eccezioni IVA. FPLS, casse ordinistiche, contributi sportivi speciali, Enasarco e tassazione personalizzata dei diritti d'autore non sono implementati. I casi interessati devono essere gestiti separatamente.
