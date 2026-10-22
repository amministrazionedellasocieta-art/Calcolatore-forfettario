# Agente di prospezione – Fisco Chiaro

Cerca sul web **pagine pubbliche e professionali** di giovani che lavorano nel digitale
(freelance, creator, social media manager, web designer, sviluppatori, community, newsletter)
e le classifica per tipo di opportunità:

| opportunita     | cosa significa                                                                 |
|-----------------|--------------------------------------------------------------------------------|
| `collaborazione`| creator/professionisti che dichiarano di accettare partnership (es. contenuti su P.IVA) |
| `community`     | gruppi, eventi, newsletter, podcast dove Fisco Chiaro può portare contenuti utili |
| `contenuti`     | pagine che mostrano i dubbi fiscali ricorrenti del target → idee editoriali     |

## Uso

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python agente.py --nicchia "social media manager" --citta Milano --max 20
python agente.py --nicchia "content creator YouTube tech"
```

I risultati si accumulano in `output/pagine_trovate.csv` (senza duplicati tra una ricerca e l'altra).
La cartella `output/` è esclusa da git.

## Cosa l'agente NON fa (e perché)

- **Non raccoglie email, telefoni o altri dati di contatto personali** (c'è anche un filtro
  che li rimuove dal CSV) e **non invia messaggi**.
- Il fatto che un dato sia pubblico online non lo rende utilizzabile per il marketing: per
  comunicazioni promozionali via email, SMS, social o messaggistica serve il **consenso
  preventivo** del destinatario (art. 130, commi 1-2, D.Lgs. 196/2003; Garante, *Linee guida
  in materia di attività promozionale e contrasto allo spam*, 4 luglio 2013, che include
  espressamente il "social spam"). Freelance e ditte individuali sono persone fisiche: si
  applica il GDPR.
- Il Garante ha sanzionato la raccolta massiva ("scraping") di recapiti dal web per creare
  elenchi da usare senza consenso.

Uso consigliato dell'elenco: proporre **collaborazioni** tramite il canale che la pagina indica
per le partnership, essere presenti nelle **community** con contenuti utili, usare le pagine
come **spunti editoriali** e come base per campagne a pagamento con targeting della piattaforma.
Se lo studio è iscritto a un Ordine, verificare anche le regole deontologiche sulla pubblicità
professionale.
