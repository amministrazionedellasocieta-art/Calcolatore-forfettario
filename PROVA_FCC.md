# Versione di prova Fisco Chiaro Consulting

## Avvio della prova

Sul branch della PR 2, installare `requirements.txt` e avviare:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app_streamlit.py
```

Questa modifica prepara l'applicazione nel repository; non pubblica un servizio online.

## Percorso del cliente

1. Compila il profilo nella barra laterale e conferma le informazioni richieste.
2. La scheda iniziale **Il tuo risultato** mostra ricavi, oneri stimati e disponibile dopo i costi. Se mancano requisiti o inquadramento, i numeri rimangono sospesi.
3. Scarica il riepilogo testuale per lo Studio. Il documento contiene dati dichiarati, ipotesi e verifiche; esclude i risultati numerici dei casi sospesi.
4. Il pulsante **Richiedi una consulenza a Fisco Chiaro** apre il modulo sul dominio ufficiale. Il cliente riporta il riepilogo nella richiesta e sceglie i recapiti sul sito dello Studio.

Il modulo ufficiale dichiara il collegamento al sistema richieste FCC. L'app non invia dati, non crea contatti nel CRM e non conferma l'avvenuta acquisizione. Il collegamento automatico del riepilogo richiede un'integrazione separata con il sistema reale: non sono stati inventati endpoint o credenziali.

## Casi di accettazione

Risultati annui a regime, aliquota sostitutiva 15%, senza agevolazioni INPS, altri redditi o detrazioni personali. I valori attesi sono fissati nei test con conteggi separati dal motore.

| Caso | Ricavi | Costi dichiarati | Contributi | Imposta | Disponibile |
| --- | ---: | ---: | ---: | ---: | ---: |
| Traduttore professionista, servizi esteri imponibili 1.000 euro inclusi nei costi | 40.000,00 | 2.000,00 | 8.133,84 | 3.459,92 | 26.186,24 |
| Affiliate marketer impresa, contratto/inquadramento confermato | 50.000,00 | 5.000,00 | 9.554,64 | 4.416,80 | 31.028,56 |
| E-commerce abbigliamento, ATECO 47.71.10 | 60.000,00 | 20.000,00 | 5.882,64 | 2.717,60 | 31.399,76 |
| Traduzione e social media professionali, 20.000 euro ciascuno | 40.000,00 | 2.000,00 | 8.133,84 | 3.459,92 | 26.406,24 |

Nel primo caso il disponibile sottrae anche 220 euro di IVA indetraibile. Attivita miste professionali/impresa: risultato sospeso, da impostare sulle singole gestioni.

## Ambito della prova

- Il piano cassa simula una nuova apertura, non ricostruisce una posizione esistente. Per il beneficio del 50% riservato agli iscritti 2025 il piano e sospeso: servono data di avvio, storico versamenti e verifica dei 36 mesi. Il calcolo annuale si riferisce al 2026, non rinnova il beneficio negli anni successivi.
- L'IVA annuale del profilo comprende soltanto servizi esteri imponibili al 22% confermati sul documento. Commissioni esenti e servizi con territorialita speciale richiedono verifica. L'analizzatore IVA considera anno precedente, importo corrente e opzioni. Accise e mezzi di trasporto nuovi richiedono adempimenti specifici.
- Il registro e uno strumento di cassa: le date dei pagamenti non sostituiscono la ricezione fattura ai fini dell'IVA. Aliquota, acquisti UE precedenti e opzione vanno indicati; il registro non genera F24.
- Le scadenze richiedono conferma del perimetro ISA e della periodicita INTRASTAT; le proroghe 2026 non sono estese automaticamente alle annualita successive.
- Confronto ordinario: addizionali medie e piena detrazione dell'IVA sui costi del modello; non simula pro-rata, detrazioni personali o prezzi B2C IVA inclusa.
- I movimenti restano nella sessione Streamlit e non sono un archivio persistente dello Studio.

Verifica locale: **192 test superati**, nessuno saltato, inclusi 10 test che eseguono l'app Streamlit. La prova resta da sottoporre alla revisione professionale dello Studio prima di distribuirla ai clienti.
