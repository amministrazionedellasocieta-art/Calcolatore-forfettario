"""Riepilogo per la versione di prova dello Studio, senza invio di dati."""
from . import diagnosi, parametri

URL_CONSULENZA = "https://www.fiscochiaroconsulting.it/?utm_source=calcolatore&utm_medium=app&utm_campaign=prova_fcc#form-preventivo"


def riepilogo(profilo: diagnosi.Profilo, esame: diagnosi.Diagnosi) -> str:
    """Esporta solo risultati utilizzabili; gli scenari sospesi restano esclusi."""
    righe = ["FISCO CHIARO CONSULTING", "Riepilogo simulazione - versione di prova",
             f"Anno d'imposta: {parametri.ANNO_IMPOSTA}",
             f"Attivita: {esame.professione.nome}",
             f"Ricavi complessivi dichiarati: {profilo.ricavi_totali:.2f} EUR",
             f"Costi dichiarati: {profilo.costi_annui:.2f} EUR"]
    if esame.stima_utilizzabile:
        e = esame.esito_forfettario
        righe += [f"Imposta sostitutiva stimata: {e.imposta_sostitutiva:.2f} EUR",
                  f"Contributi stimati: {e.contributi_dovuti:.2f} EUR",
                  f"Disponibile dopo costi e oneri: {esame.netto_reale:.2f} EUR",
                  "Ipotesi annua a regime, non importi F24; costi e contributi versati da confermare.",
                  "Servizi esteri: inclusi solo quelli imponibili al 22% dichiarati nel profilo."]
    else:
        righe += ["STIMA SOSPESA: completare inquadramento e requisiti prima dei calcoli."]
    righe += ["", "Attivita dichiarate:"]
    righe += [f"- {a.professione.nome}: {a.ricavi:.2f} EUR; ATECO {a.professione.ateco or 'da definire'}" for a in esame.attivita]
    righe += ["", "Verifiche da approfondire:"]
    righe += [f"- {v.nome}: {v.messaggio}" for v in esame.verifiche if v.esito != diagnosi.OK]
    if profilo.riduzione_richiesta == 50:
        righe += ["Piano cassa sospeso: servono data di avvio 2025, storico e verifica dei 36 mesi."]
    righe += ["", "Riepilogo non ancora validato dallo Studio e non inviato automaticamente.",
              "Richiedi la consulenza sul sito ufficiale e riporta questo riepilogo nel modulo.",
              URL_CONSULENZA]
    return "\n".join(righe)
