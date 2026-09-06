# Fisco Digitale

Fiscalità e contabilità per i lavori digitali — anno d'imposta 2026.

I simulatori di regime forfettario online chiedono "quanto fatturi" e "che
coefficiente hai". Ma chi fa lo streamer, vende su Amazon FBA o incassa da
Dublino non conosce il proprio coefficiente: conosce il proprio lavoro. E le
domande che gli servono non sono nel simulatore.

Questo progetto parte dal lavoro reale e arriva a tutto il resto: codice ATECO,
coefficiente, cassa previdenziale, adempimenti, trattamento IVA delle piattaforme
estere, scadenze, soglie e cassa dei primi anni.

## Cosa fa, in concreto

**44 professioni digitali mappate** — influencer, streamer, YouTuber, creator in
abbonamento, sviluppatori, consulenti AI, designer, social media manager, media
buyer, e-commerce, dropshipping, Amazon FBA, print on demand, infoprodotti,
formatori, traduttori, virtual assistant, artisti NFT, investitori in
cripto-attività. Per ciascuna: codice ATECO 2025, coefficiente di redditività,
inquadramento previdenziale, obbligo camerale, note e trappole tipiche.

**Il trattamento IVA delle piattaforme** — la parte che manca ovunque. Chi ti
paga davvero (Google Ireland, Fenix International, Amazon Lussemburgo), che
documento emettere, quale dicitura scrivere, se serve il VIES, quando scatta
l'OSS. E soprattutto: quanto ti costa l'IVA in inversione contabile sugli
acquisti esteri, che nel forfettario non recuperi mai.

**La cassa dei primi anni, non solo la competenza** — il primo anno versi poco o
nulla, il secondo arrivano insieme il saldo del primo e gli acconti del secondo.
È il punto in cui la maggior parte dei freelance si trova scoperta. Il piano di
cassa applica le regole reali: acconto d'imposta al 100%, acconto della Gestione
Separata all'80%, quota fissa artigiani e commercianti in quattro rate durante
l'anno.

**Il confronto onesto con l'ordinario** — con il calcolo del punto di pareggio:
oltre quanti costi reali il forfettario inizia a farti perdere soldi. Per un
professionista al 78% il pareggio è intorno al 34% dei ricavi, per uno
sviluppatore al 67% al 42%, per un e-commerce al 40% al 74%. Il regime
ordinario è calcolato con la detrazione per redditi di lavoro autonomo
(art. 13 c. 5 TUIR): ignorarla sposterebbe il pareggio di circa due punti e
sempre nella stessa direzione.

**L'inquadramento non lo indovina** — per i lavori che possono essere
professionali o d'impresa (streamer, videomaker, affiliate marketer, coach) la
cassa previdenziale non si deduce dal fatturato: dipende da come è organizzata
l'attività. Lo strumento lo dichiara come scelta aperta, mostra quanto costa
l'una e l'altra forma e chiede all'utente di indicarlo.

**Contabilità di cassa con presidio delle soglie** — 85.000 e 100.000 euro,
10.000 euro di vendite a privati UE, 10.000 euro di acquisti di beni UE, 20.000
euro di costo del personale. Con proiezione a fine anno e quota da accantonare
su ogni incasso.

**Scadenzario filtrato** sul profilo reale: chi non compra servizi esteri non
vede le dodici scadenze mensili dell'inversione contabile.

## Come si usa

```bash
pip install -r requirements.txt
streamlit run app_streamlit.py
```

Da riga di comando, senza browser:

```bash
python3 -m fiscodigitale --elenco
python3 -m fiscodigitale --cerca twitch
python3 -m fiscodigitale --professione dropshipping --ricavi 60000 --costi 35000 --esteri 4000
```

Come libreria:

```python
from fiscodigitale import diagnosi

esito = diagnosi.analizza(
    diagnosi.Profilo(
        professione="streamer",
        ricavi_attesi=45_000,
        clienti_esteri_b2b=True,
        acquisti_servizi_esteri=3_000,
    )
)
print(esito.sintesi())
print(esito.netto_reale)
```

## Architettura

Il motore non importa Streamlit: l'interfaccia è sostituibile e i calcoli sono
testabili in isolamento.

| Modulo | Responsabilità |
| --- | --- |
| `parametri.py` | Tutti i valori 2026 in un solo posto, con le fonti. L'aggiornamento annuale tocca questo file |
| `professioni.py` | Catalogo delle professioni digitali e ricerca per lavoro, piattaforma o codice |
| `previdenza.py` | Gestione Separata e Artigiani/Commercianti, riduzioni contributive, ragguaglio mensile |
| `forfettario.py` | Imposta sostitutiva, acconti, piano di cassa pluriennale, ricavi necessari per un netto obiettivo |
| `ordinario.py` | IRPEF a scaglioni 2026, addizionali, contributi deducibili |
| `confronto.py` | Confronto tra regimi e punto di pareggio dei costi |
| `iva_estero.py` | Territorialità IVA, reverse charge, OSS, database delle piattaforme |
| `contabilita.py` | Registro di cassa, soglie, proiezioni, accantonamento |
| `scadenze.py` | Scadenzario personalizzato, con spostamento delle date festive |
| `diagnosi.py` | Orchestrazione: dal lavoro alla checklist completa |

```bash
python3 -m unittest discover -s tests -v   # 85 test
```

## Dati e fonti

Valori aggiornati all'anno d'imposta 2026:

- soglie del forfettario 85.000 / 100.000 euro, limite di 35.000 euro per i
  redditi da lavoro dipendente dell'anno precedente;
- Gestione Separata al 26,07%, minimale 18.808 euro, massimale 122.295 euro
  (circolare INPS n. 8/2026);
- artigiani e commercianti: quota fissa 4.521,36 e 4.611,64 euro, minimale
  18.808 euro, secondo scaglione da 56.224 euro (circolare INPS n. 14/2026);
- IRPEF 2026 a tre aliquote 23% / 33% / 43%;
- cripto-attività al 33% dal 1° gennaio 2026, senza più la soglia di esenzione;
- riduzione contributiva del 50% non più richiedibile da nuovi iscritti dal
  1° gennaio 2026: resta a chi si è iscritto nel 2025, per 36 mesi;
- forfettari esclusi dal concordato preventivo biennale;
- codici ATECO nella classificazione 2025, in vigore dal 1° aprile 2025.

I coefficienti di redditività restano quelli dell'Allegato 4 della L. 190/2014,
agganciati all'attività corrispondente della vecchia classificazione: la tabella
riscritta su ATECO 2025 non è ancora stata adottata.

## Limiti

Lo strumento produce stime e orientamento, non sostituisce un commercialista.
In particolare:

- l'inquadramento di molti lavori digitali dipende da **come** l'attività è
  organizzata in concreto (professionale o d'impresa), e il codice ATECO va
  confermato caso per caso;
- il calcolo in regime ordinario applica la detrazione per redditi di lavoro
  autonomo, ma non le detrazioni personali, i familiari a carico e gli oneri
  detraibili, che riducono ulteriormente il dovuto;
- le addizionali regionali e comunali usano valori medi, non quelli del tuo
  Comune;
- l'entità che paga una piattaforma può cambiare nel tempo: va sempre verificata
  sul contratto o sull'estratto conto prima di impostare la fatturazione.

## Da fare

- coefficienti aggiornati quando uscirà la tabella riscritta su ATECO 2025;
- casse professionali con i regolamenti reali al posto dei parametri indicativi;
- import dei movimenti da CSV di banca e piattaforme;
- calcolo delle plusvalenze su cripto-attività con il metodo LIFO;
- attività multiple: chi incassa da sponsorizzazioni (78%) e da AdSense (67%)
  oggi deve sceglierne una sola;
- rimozione o implementazione dei parametri dichiarati e non ancora usati
  (casse professionali, diritti d'autore, ritenuta d'acconto, IRAP).
