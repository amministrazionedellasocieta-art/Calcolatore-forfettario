# Revisione del motore fiscale — 17 ottobre 2026

Correzioni successive alla versione `059fa4c` della PR 2.

- IVA oltre 100.000 euro: decorre dall'operazione che provoca il superamento e dalle successive; il reddito segue invece le regole ordinarie per l'intero anno. Corretto anche il registro: il solo raggiungimento della soglia non equivale al superamento.
- Crediti nel piano di cassa: gli acconti assolti mediante compensazione restano conteggiati come versati al saldo successivo. Nel caso Gestione Separata, ricavi 50.000 euro e coefficiente 78%, il quarto anno versa 5.544,97 euro di imposte, invece di 8.290,14.
- Rate fisse INPS: la quota di ottobre-dicembre viene pagata e dedotta a febbraio dell'anno successivo. Con apertura a gennaio senza riduzioni e contributo annuo commercianti di 4.611,64 euro, il primo anno paga 3.458,73 euro e il secondo 4.611,64.
- IVA sui servizi esteri: il costo indetraibile entra nel confronto tra regimi e nella ricerca del pareggio, oltre che nella diagnosi. Il grafico usa lo stesso parametro.
- Detrazione art. 13 TUIR: aggiunta la maggiorazione di 50 euro per reddito complessivo superiore a 11.000 e non superiore a 17.000 euro.
- Aliquota 5%: nessuna applicazione automatica. La nuova apertura richiede conferma esplicita dei tre requisiti del comma 65. La stessa regola vale per la libreria; in CLI usare `--startup-confermata` solo dopo averli verificati. Il piano termina l'agevolazione dopo il quinto periodo.

## Ipotesi del calcolo

Il piano simula una nuova apertura: senza una data di avvio esplicita, un numero di mesi inferiore a dodici indica apertura all'inizio del mese `13 - mesi_attivita`. Negli anni successivi si considerano dodici mesi. Parametri annuali, gestione previdenziale e riduzione contributiva rimangono costanti: non e' un calendario F24 personalizzato e non gestisce automaticamente la scadenza dei 36 mesi dell'agevolazione INPS al 50%.

I costi del confronto comprendono i servizi esteri al netto dell'IVA da inversione contabile. Quest'ultima e' un costo aggiuntivo nel forfettario; nel confronto ordinario si assume piena detraibilita'. Non e' un confronto tra prezzi B2C IVA inclusa. Il grafico varia i costi mantenendo invariato l'importo inserito di acquisti esteri.

L'aggiornamento corregge i casi indicati; non costituisce validazione completa del catalogo ATECO e dei coefficienti, delle gestioni previdenziali, della scadenza delle agevolazioni, delle eccezioni IVA e del riparto degli acconti. Rimangono da verificare prima dell'uso autonomo da parte dei clienti. Il 5% e' una dichiarazione dell'utilizzatore sui requisiti, non una certificazione automatica della loro esistenza.

## Fonti verificate

- L. 190/2014, art. 1, commi 65 e 71: https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:2014;190
- TUIR, art. 13, comma 5-ter: https://www.normattiva.it/atto/caricaDettaglioAtto?atto.articolo.numero=13&atto.codiceRedazionale=086U0917&atto.dataPubblicazioneGazzetta=1986-12-31&vigenza=2026-01-01
- INPS, aliquote e versamenti commercianti: https://www.inps.it/it/it/dettaglio-approfondimento.schede-informative.49849.aliquote-e-contributi-commercianti.html

## Verifica

`python3 -m unittest discover -s tests`: 149 test, incluso Streamlit.
I nuovi casi di regressione hanno riprodotto i difetti prima della correzione.


## Successiva revisione del catalogo

Completato il confronto delle 44 schede con struttura, note e raccordo ISTAT aggiornato 2026; criteri e ambiti supportati sono in [VERIFICA_CATALOGO.md](VERIFICA_CATALOGO.md). Questa fase aggiunge sospensione dei numeri per dati incompleti, casi FPLS e previdenza mista. Non equivale a validazione integrale di tutti i moduli fiscali.


## Correzione di scadenze OSS e massimale INPS

- L'OSS scade il 30 aprile, 31 luglio, 31 ottobre e 31 gennaio successivo. Questi termini non vengono rinviati al lunedi' se cadono nel fine settimana. Nel 2026 il terzo trimestre resta al 31 ottobre (sabato); il quarto al 31 gennaio 2027 (domenica).
- Il massimale annuale artigiani/commercianti di 122.295 euro, adottato dal motore per i soggetti privi di anzianita' contributiva al 31 dicembre 1995, non viene piu' moltiplicato per i mesi/12. Rimane il ragguaglio del minimale e del contributo fisso. La modifica non introduce il diverso massimale per i soggetti con anzianita' pregressa.
- Sette nuovi test verificano date, mancato rinvio OSS, calendario delle prossime scadenze, conservazione dello slittamento ordinario dei weekend, massimale per periodi di uno/tre/sei/dodici mesi e quota fissa.

Fonti: [Commissione europea, dichiarazione e pagamento OSS](https://vat-one-stop-shop.ec.europa.eu/one-stop-shop/declare-and-pay-oss_en), [INPS 14/2026, paragrafo 4](https://www.inps.it/content/dam/inps-site/it/scorporati/circolari-e-messaggi/2026/02/Circolare_15162/Allegati/16561_Circolare-numero-14-del-09-02-2026.pdf).
