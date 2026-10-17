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
