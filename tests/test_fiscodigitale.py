"""Test del motore fiscale. Si eseguono con: python3 -m unittest discover -s tests"""

import unittest
from datetime import date

from fiscodigitale import (
    confronto,
    contabilita,
    cripto,
    formato,
    diagnosi,
    forfettario,
    iva_estero,
    ordinario,
    parametri as P,
    previdenza,
    professioni,
    scadenze,
)


class TestCatalogo(unittest.TestCase):
    def test_slug_unici(self):
        slugs = [p.slug for p in professioni.CATALOGO]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_coefficienti_validi(self):
        for p in professioni.CATALOGO:
            self.assertIn(p.gruppo_coefficiente, P.COEFFICIENTI, p.slug)
            self.assertTrue(0 < p.coefficiente <= 1)

    def test_gestione_dichiarata(self):
        for p in professioni.CATALOGO:
            self.assertIn(p.gestione_inps, professioni.LABEL_GESTIONE, p.slug)

    def test_ricerca_trova_per_piattaforma(self):
        risultati = professioni.cerca("twitch")
        self.assertTrue(any(p.slug == "streamer" for p in risultati))

    def test_ricerca_vuota_restituisce_catalogo(self):
        self.assertTrue(professioni.cerca(""))

    def test_impresa_richiede_camera_commercio(self):
        for p in professioni.CATALOGO:
            if p.gestione_inps == professioni.COMMERCIANTI:
                self.assertTrue(p.camera_commercio, p.slug)


class TestPrevidenza(unittest.TestCase):
    def test_gestione_separata_percentuale(self):
        c = previdenza.gestione_separata(20_000)
        self.assertAlmostEqual(c.totale, 20_000 * 0.2607, places=2)

    def test_gestione_separata_rispetta_massimale(self):
        c = previdenza.gestione_separata(200_000)
        atteso = P.GESTIONE_SEPARATA["massimale"] * 0.2607
        self.assertAlmostEqual(c.totale, atteso, places=2)

    def test_commercianti_sotto_minimale_paga_il_fisso(self):
        c = previdenza.artigiani_commercianti(3_000, gestione=previdenza.COMMERCIANTI)
        self.assertAlmostEqual(c.totale, P.COMMERCIANTI["contributo_fisso"], places=2)

    def test_commercianti_eccedenza(self):
        c = previdenza.artigiani_commercianti(30_000, gestione=previdenza.COMMERCIANTI)
        eccedenza = (30_000 - P.MINIMALE_ARTIGIANI_COMMERCIANTI) * P.COMMERCIANTI["aliquota_ivs"]
        self.assertAlmostEqual(c.quota_variabile, eccedenza, places=2)

    def test_secondo_scaglione(self):
        c = previdenza.artigiani_commercianti(70_000, gestione=previdenza.ARTIGIANI)
        primo = (P.SCAGLIONE_ARTIGIANI_COMMERCIANTI - P.MINIMALE_ARTIGIANI_COMMERCIANTI) * 0.24
        secondo = (70_000 - P.SCAGLIONE_ARTIGIANI_COMMERCIANTI) * 0.25
        self.assertAlmostEqual(c.quota_variabile, primo + secondo, places=2)

    def test_riduzione_35_su_tutta_la_contribuzione(self):
        piena = previdenza.artigiani_commercianti(30_000, gestione=previdenza.COMMERCIANTI)
        ridotta = previdenza.artigiani_commercianti(
            30_000, gestione=previdenza.COMMERCIANTI, riduzione=35
        )
        self.assertAlmostEqual(ridotta.totale, piena.totale * 0.65, places=2)

    def test_riduzione_50_lascia_intera_la_maternita(self):
        ridotta = previdenza.artigiani_commercianti(
            10_000, gestione=previdenza.COMMERCIANTI, riduzione=50
        )
        ivs = P.COMMERCIANTI["contributo_fisso"] - P.CONTRIBUTO_MATERNITA
        self.assertAlmostEqual(ridotta.totale, ivs * 0.5 + P.CONTRIBUTO_MATERNITA, places=2)

    def test_riduzione_50_non_piu_richiedibile_da_nuovi_iscritti(self):
        self.assertFalse(P.RIDUZIONE_50_APERTA_A_NUOVE_ISCRIZIONI)
        self.assertEqual(
            previdenza.riduzioni_disponibili(previdenza.COMMERCIANTI), (0, 35)
        )
        self.assertIn(
            50, previdenza.riduzioni_disponibili(previdenza.COMMERCIANTI, prima_iscrizione_2025=True)
        )

    def test_ragguaglio_mesi(self):
        c = previdenza.artigiani_commercianti(
            0, gestione=previdenza.ARTIGIANI, mesi_attivita=6
        )
        self.assertAlmostEqual(c.totale, P.ARTIGIANI["contributo_fisso"] / 2, places=2)

    def test_riduzione_non_valida(self):
        with self.assertRaises(ValueError):
            previdenza.artigiani_commercianti(10_000, gestione=previdenza.ARTIGIANI, riduzione=20)


class TestForfettario(unittest.TestCase):
    def situazione(self, **kwargs):
        base = dict(
            ricavi=50_000,
            coefficiente=0.78,
            gestione=previdenza.GESTIONE_SEPARATA,
            contributi_versati=0.0,
        )
        base.update(kwargs)
        return forfettario.Situazione(**base)

    def test_imposta_senza_deduzione(self):
        e = forfettario.calcola(self.situazione())
        self.assertAlmostEqual(e.reddito_forfetario, 39_000, places=2)
        self.assertAlmostEqual(e.imposta_sostitutiva, 39_000 * 0.15, places=2)

    def test_aliquota_startup(self):
        e = forfettario.calcola(self.situazione(startup=True))
        self.assertAlmostEqual(e.imposta_sostitutiva, 39_000 * 0.05, places=2)

    def test_contributi_deducibili_riducono_imponibile(self):
        e = forfettario.calcola(self.situazione(contributi_versati=10_000))
        self.assertAlmostEqual(e.imponibile, 29_000, places=2)

    def test_deduzione_non_genera_imponibile_negativo(self):
        e = forfettario.calcola(self.situazione(ricavi=5_000, contributi_versati=20_000))
        self.assertEqual(e.imponibile, 0.0)
        self.assertEqual(e.imposta_sostitutiva, 0.0)

    def test_avviso_oltre_soglia(self):
        e = forfettario.calcola(self.situazione(ricavi=90_000))
        self.assertTrue(any("dal prossimo" in a for a in e.avvisi))

    def test_avviso_uscita_immediata(self):
        e = forfettario.calcola(self.situazione(ricavi=120_000))
        self.assertTrue(any("immediatamente" in a for a in e.avvisi))

    def test_validazione_input(self):
        with self.assertRaises(ValueError):
            forfettario.Situazione(ricavi=-1, coefficiente=0.78)
        with self.assertRaises(ValueError):
            forfettario.Situazione(ricavi=1000, coefficiente=78)
        with self.assertRaises(ValueError):
            forfettario.Situazione(ricavi=1000, coefficiente=0.78, mesi_attivita=13)

    def test_acconti_sotto_soglia(self):
        self.assertFalse(forfettario.acconti(40).dovuto)

    def test_acconti_unica_rata(self):
        a = forfettario.acconti(200)
        self.assertEqual(a.prima_rata, 0.0)
        self.assertAlmostEqual(a.seconda_rata, 200, places=2)

    def test_acconti_due_rate(self):
        a = forfettario.acconti(1_000)
        self.assertAlmostEqual(a.prima_rata, 400, places=2)
        self.assertAlmostEqual(a.seconda_rata, 600, places=2)

    def test_piano_cassa_primo_anno_senza_imposte(self):
        piano = forfettario.piano_cassa(self.situazione(contributi_versati=None), anni=3)
        self.assertEqual(piano[0].imposta_cassa, 0.0)
        self.assertGreater(piano[1].uscite_cassa, piano[0].uscite_cassa)

    def test_piano_cassa_gestione_separata_primo_anno_nulla(self):
        piano = forfettario.piano_cassa(
            self.situazione(contributi_versati=None, gestione=previdenza.GESTIONE_SEPARATA), anni=2
        )
        self.assertEqual(piano[0].uscite_cassa, 0.0)

    def test_piano_cassa_commercianti_paga_subito_il_fisso(self):
        piano = forfettario.piano_cassa(
            self.situazione(contributi_versati=None, gestione=previdenza.COMMERCIANTI), anni=2
        )
        self.assertGreater(piano[0].contributi_cassa, 0)

    def test_ricavi_per_netto_obiettivo(self):
        s = self.situazione(contributi_versati=None)
        ricavi = forfettario.ricavi_per_netto_obiettivo(30_000, s)
        netto = forfettario.calcola(
            forfettario.Situazione(
                ricavi=ricavi,
                coefficiente=s.coefficiente,
                gestione=s.gestione,
                contributi_versati=None,
            )
        ).netto
        self.assertAlmostEqual(netto, 30_000, delta=5)


class TestOrdinario(unittest.TestCase):
    def test_scaglioni_irpef(self):
        imposta, _ = ordinario.irpef(28_000)
        self.assertAlmostEqual(imposta, 28_000 * 0.23, places=2)

    def test_secondo_scaglione_al_33(self):
        imposta, _ = ordinario.irpef(50_000)
        atteso = 28_000 * 0.23 + 22_000 * 0.33
        self.assertAlmostEqual(imposta, atteso, places=2)

    def test_terzo_scaglione(self):
        imposta, _ = ordinario.irpef(70_000)
        atteso = 28_000 * 0.23 + 22_000 * 0.33 + 20_000 * 0.43
        self.assertAlmostEqual(imposta, atteso, places=2)

    def test_aliquota_marginale(self):
        self.assertEqual(ordinario.aliquota_marginale(30_000), 0.33)
        self.assertEqual(ordinario.aliquota_marginale(80_000), 0.43)

    def test_detrazione_scaglione_pieno(self):
        self.assertEqual(ordinario.detrazione_lavoro_autonomo(3_000), 1_265.0)
        self.assertEqual(ordinario.detrazione_lavoro_autonomo(5_500), 1_265.0)

    def test_detrazione_continua_nei_raccordi(self):
        # La funzione non deve avere salti nei due punti di raccordo.
        self.assertAlmostEqual(
            ordinario.detrazione_lavoro_autonomo(5_500.01), 1_265.0, delta=0.01
        )
        self.assertAlmostEqual(
            ordinario.detrazione_lavoro_autonomo(28_000), 500.0, places=2
        )
        self.assertAlmostEqual(
            ordinario.detrazione_lavoro_autonomo(28_000.01), 500.0, delta=0.01
        )

    def test_detrazione_si_azzera_a_50000(self):
        self.assertEqual(ordinario.detrazione_lavoro_autonomo(50_000), 0.0)
        self.assertEqual(ordinario.detrazione_lavoro_autonomo(90_000), 0.0)

    def test_detrazione_decrescente(self):
        valori = [ordinario.detrazione_lavoro_autonomo(r) for r in range(0, 60_000, 2_000)]
        self.assertEqual(valori, sorted(valori, reverse=True))

    def test_detrazione_applicata_riduce_irpef(self):
        e = ordinario.calcola(ordinario.SituazioneOrdinario(ricavi=40_000))
        self.assertGreater(e.detrazione, 0)
        self.assertAlmostEqual(e.irpef, e.irpef_lorda - e.detrazione, places=2)

    def test_detrazione_non_genera_credito(self):
        e = ordinario.calcola(ordinario.SituazioneOrdinario(ricavi=6_000))
        self.assertGreaterEqual(e.irpef, 0.0)
        self.assertLessEqual(e.detrazione, e.irpef_lorda)

    def test_addizionali_non_dovute_se_irpef_azzerata(self):
        e = ordinario.calcola(ordinario.SituazioneOrdinario(ricavi=6_000))
        self.assertEqual(e.irpef, 0.0)
        self.assertEqual(e.addizionali, 0.0)

    def test_detrazione_parametrata_al_reddito_complessivo(self):
        # Non all'imponibile al netto dei contributi: due redditi complessivi
        # uguali danno la stessa detrazione a parita' di gestione.
        a = ordinario.calcola(ordinario.SituazioneOrdinario(ricavi=40_000, costi=0))
        b = ordinario.calcola(ordinario.SituazioneOrdinario(ricavi=50_000, costi=10_000))
        self.assertEqual(a.detrazione, b.detrazione)

    def test_contributi_deducibili(self):
        e = ordinario.calcola(ordinario.SituazioneOrdinario(ricavi=50_000, costi=10_000))
        self.assertAlmostEqual(e.reddito, 40_000, places=2)
        self.assertAlmostEqual(
            e.imponibile_irpef, 40_000 - e.contributi_dovuti, places=2
        )


class TestConfronto(unittest.TestCase):
    def base(self, coefficiente=0.78, gestione=previdenza.GESTIONE_SEPARATA, riduzione=0):
        return forfettario.Situazione(
            ricavi=50_000,
            coefficiente=coefficiente,
            gestione=gestione,
            riduzione=riduzione,
            contributi_versati=None,
        )

    def test_senza_costi_conviene_il_forfettario(self):
        c = confronto.confronta(self.base(), costi=0)
        self.assertEqual(c.conviene, "forfettario")

    def test_costi_alti_ribaltano_il_confronto(self):
        c = confronto.confronta(self.base(), costi=40_000)
        self.assertEqual(c.conviene, "ordinario")

    def test_pareggio_coerente(self):
        s = self.base()
        pareggio = confronto.costi_di_pareggio(s)
        self.assertIsNotNone(pareggio)
        sotto = confronto.confronta(s, costi=pareggio - 5_000)
        sopra = confronto.confronta(s, costi=pareggio + 5_000)
        self.assertEqual(sotto.conviene, "forfettario")
        self.assertEqual(sopra.conviene, "ordinario")

    def test_detrazione_abbassa_il_pareggio(self):
        # Applicare la detrazione rende l'ordinario meno caro, quindi il
        # pareggio arriva prima: e' la correzione al confronto tra regimi.
        pareggio = confronto.costi_di_pareggio(self.base())
        self.assertLess(pareggio, 17_648)

    def test_coefficiente_basso_alza_il_pareggio(self):
        alto = confronto.costi_di_pareggio(self.base(coefficiente=0.78))
        basso = confronto.costi_di_pareggio(
            self.base(coefficiente=0.40, gestione=previdenza.COMMERCIANTI)
        )
        self.assertGreater(basso, alto)

    def test_costi_reali_scontati_da_entrambi_i_regimi(self):
        c = confronto.confronta(self.base(), costi=10_000)
        self.assertAlmostEqual(
            c.netto_forfettario, c.esito_forfettario.netto - 10_000, places=2
        )


class TestIvaEstero(unittest.TestCase):
    def test_vendita_ue_b2b_reverse_charge(self):
        e = iva_estero.analizza(iva_estero.Operazione(area=iva_estero.UE))
        self.assertEqual(e.natura, "N2.1")
        self.assertIn("7-ter", e.riferimento)
        self.assertTrue(any("VIES" in a for a in e.adempimenti))

    def test_vendita_italia_forfettario_senza_iva(self):
        e = iva_estero.analizza(iva_estero.Operazione(area=iva_estero.ITALIA))
        self.assertEqual(e.natura, "N2.2")
        self.assertIn("bollo", " ".join(e.adempimenti).lower())

    def test_cessione_beni_ue_forfettario_non_intracomunitaria(self):
        e = iva_estero.analizza(
            iva_estero.Operazione(area=iva_estero.UE, oggetto=iva_estero.BENE)
        )
        self.assertIn("2-bis", e.riferimento)

    def test_cessione_beni_ue_ordinario_non_imponibile(self):
        e = iva_estero.analizza(
            iva_estero.Operazione(
                area=iva_estero.UE, oggetto=iva_estero.BENE, regime=iva_estero.ORDINARIO
            )
        )
        self.assertEqual(e.natura, "N3.2")

    def test_soglia_oss_servizi_elettronici(self):
        sotto = iva_estero.analizza(iva_estero.Operazione(
            oggetto=iva_estero.SERVIZIO_ELETTRONICO, controparte=iva_estero.B2C,
            area=iva_estero.UE, vendite_ue_b2c_anno=5_000,
        ))
        sopra = iva_estero.analizza(iva_estero.Operazione(
            oggetto=iva_estero.SERVIZIO_ELETTRONICO, controparte=iva_estero.B2C,
            area=iva_estero.UE, vendite_ue_b2c_anno=15_000,
        ))
        self.assertIn("sotto soglia", sotto.titolo)
        self.assertIn("OSS", sopra.riferimento)

    def test_acquisto_servizi_esteri_sempre_reverse_charge(self):
        e = iva_estero.analizza(iva_estero.Operazione(
            direzione=iva_estero.ACQUISTO, area=iva_estero.EXTRA_UE
        ))
        self.assertIn("TD17", e.documento)

    def test_acquisto_beni_ue_sotto_soglia_forfettario(self):
        e = iva_estero.analizza(iva_estero.Operazione(
            direzione=iva_estero.ACQUISTO, area=iva_estero.UE, oggetto=iva_estero.BENE,
            acquisti_beni_ue_anno=2_000, importo=1_000,
        ))
        self.assertIn("sotto soglia", e.titolo)

    def test_acquisto_beni_ue_sopra_soglia_forfettario(self):
        e = iva_estero.analizza(iva_estero.Operazione(
            direzione=iva_estero.ACQUISTO, area=iva_estero.UE, oggetto=iva_estero.BENE,
            acquisti_beni_ue_anno=20_000, importo=1_000,
        ))
        self.assertIn("TD18", e.documento)

    def test_piattaforme_hanno_area_valida(self):
        for p in iva_estero.PIATTAFORME:
            self.assertIn(p.area, (iva_estero.ITALIA, iva_estero.UE, iva_estero.EXTRA_UE))
            self.assertIn(p.ruolo, ("committente", "fornitore", "entrambi"))

    def test_analisi_piattaforma_fornitore_e_acquisto(self):
        _, esito = iva_estero.analizza_piattaforma("google-ads")
        self.assertIn("TD17", esito.documento)

    def test_natura_ha_una_descrizione(self):
        e = iva_estero.analizza(iva_estero.Operazione(area=iva_estero.UE))
        self.assertIn("7-septies", e.natura_descrizione)

    def test_natura_assente_non_rompe(self):
        e = iva_estero.analizza(iva_estero.Operazione(
            direzione=iva_estero.ACQUISTO, area=iva_estero.UE
        ))
        self.assertEqual(e.natura_descrizione, "")

    def test_iva_reverse_charge(self):
        self.assertAlmostEqual(iva_estero.iva_reverse_charge(1_000), 220.0, places=2)


class TestScadenze(unittest.TestCase):
    def test_calendario_ordinato(self):
        cal = scadenze.calendario(2026)
        self.assertEqual(list(cal), sorted(cal, key=lambda s: s.data))

    def test_nessuna_scadenza_nel_weekend(self):
        for s in scadenze.calendario(2026, scadenze.Profilo(acquisti_esteri=True)):
            self.assertLess(s.data.weekday(), 5, s.titolo)

    def test_artigiani_hanno_le_rate_fisse(self):
        cal = scadenze.calendario(2026, scadenze.Profilo(gestione=previdenza.COMMERCIANTI))
        rate = [s for s in cal if "fissi" in s.titolo]
        self.assertEqual(len(rate), 4)

    def test_acquisti_esteri_generano_scadenze_mensili(self):
        cal = scadenze.calendario(2026, scadenze.Profilo(acquisti_esteri=True))
        versamenti = [s for s in cal if "inversione contabile" in s.titolo]
        self.assertEqual(len(versamenti), 12)

    def test_prossime_sono_future(self):
        oggi = date(2026, 9, 6)
        for s in scadenze.prossime(5, da=oggi):
            self.assertGreaterEqual(s.data, oggi)


class TestContabilita(unittest.TestCase):
    def registro(self):
        r = contabilita.Registro(2026)
        r.aggiungi(contabilita.Movimento(date(2026, 1, 15), "Cliente IT", 10_000))
        r.aggiungi(contabilita.Movimento(
            date(2026, 2, 15), "Piattaforma UE", 20_000, area=iva_estero.UE
        ))
        r.aggiungi(contabilita.Movimento(
            date(2026, 3, 15), "Ads", 5_000, tipo=contabilita.SPESA, area=iva_estero.UE
        ))
        return r

    def test_totali(self):
        r = self.registro()
        self.assertEqual(r.incassi, 30_000)
        self.assertEqual(r.spese, 5_000)

    def test_iva_reverse_charge_solo_su_spese_estere(self):
        self.assertAlmostEqual(self.registro().iva_reverse_charge_maturata, 1_100, places=2)

    def test_movimento_anno_sbagliato(self):
        with self.assertRaises(ValueError):
            contabilita.Registro(2026).aggiungi(
                contabilita.Movimento(date(2025, 1, 1), "vecchio", 100)
            )

    def test_importo_negativo_rifiutato(self):
        with self.assertRaises(ValueError):
            contabilita.Movimento(date(2026, 1, 1), "x", -5)

    def test_proiezione_annuale(self):
        r = self.registro()
        proiezione = r.proiezione_annuale(date(2026, 6, 30))
        self.assertGreater(proiezione, r.incassi)

    def test_soglia_superata(self):
        r = contabilita.Registro(2026)
        r.aggiungi(contabilita.Movimento(date(2026, 5, 1), "big", 95_000))
        soglie = {s.nome: s for s in r.soglie(date(2026, 5, 2))}
        self.assertEqual(soglie["Permanenza nel forfettario"].stato, "superata")
        self.assertTrue(any("SUPERATA" in a for a in r.allerte(date(2026, 5, 2))))

    def test_accantonamento_coerente(self):
        r = self.registro()
        s = forfettario.Situazione(
            ricavi=0, coefficiente=0.78, gestione=previdenza.GESTIONE_SEPARATA
        )
        acc = r.accantonamento(s, date(2026, 6, 30))
        self.assertGreater(acc["quota_su_ogni_incasso"], 0.2)
        self.assertEqual(acc["iva_estera_da_versare"], 1_100)


class TestDiagnosi(unittest.TestCase):
    def test_diagnosi_completa(self):
        d = diagnosi.analizza(
            diagnosi.Profilo(
                professione="sviluppatore-software",
                ricavi_attesi=40_000,
                clienti_esteri_b2b=True,
                acquisti_servizi_esteri=2_000,
            ),
            oggi=date(2026, 9, 6),
        )
        self.assertTrue(d.ammesso_al_forfettario)
        self.assertEqual(d.gestione, previdenza.GESTIONE_SEPARATA)
        self.assertTrue(d.adempimenti)
        self.assertTrue(any("VIES" in a.titolo for a in d.adempimenti))
        self.assertAlmostEqual(d.iva_estera_annua, 440, places=2)

    def test_redditi_dipendente_oltre_soglia_bloccano(self):
        d = diagnosi.analizza(
            diagnosi.Profilo(
                professione="copywriter",
                ricavi_attesi=20_000,
                redditi_dipendente_anno_precedente=40_000,
            )
        )
        self.assertFalse(d.ammesso_al_forfettario)

    def test_partecipazioni_bloccano(self):
        d = diagnosi.analizza(
            diagnosi.Profilo(
                professione="copywriter", ricavi_attesi=20_000, partecipazioni_societarie=True
            )
        )
        self.assertFalse(d.ammesso_al_forfettario)

    def test_inquadramento_incerto_viene_segnalato(self):
        d = diagnosi.analizza(diagnosi.Profilo(professione="streamer", ricavi_attesi=45_000))
        self.assertTrue(d.inquadramento_da_scegliere)
        self.assertEqual(d.gestione, previdenza.GESTIONE_SEPARATA)
        self.assertTrue(any(v.nome == "Inquadramento da confermare" for v in d.verifiche))

    def test_inquadramento_non_dipende_dal_fatturato(self):
        # Regressione: prima una soglia arbitraria di 30.000 euro decideva la
        # cassa previdenziale al posto dell'utente.
        bassi = diagnosi.analizza(diagnosi.Profilo(professione="streamer", ricavi_attesi=12_000))
        alti = diagnosi.analizza(diagnosi.Profilo(professione="streamer", ricavi_attesi=80_000))
        self.assertEqual(bassi.gestione, alti.gestione)

    def test_natura_esplicita_risolve_la_scelta(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="streamer", ricavi_attesi=45_000, natura_attivita=diagnosi.IMPRESA
        ))
        self.assertFalse(d.inquadramento_da_scegliere)
        self.assertEqual(d.gestione, previdenza.COMMERCIANTI)
        self.assertFalse(any(v.nome == "Inquadramento da confermare" for v in d.verifiche))

    def test_natura_professionale_esplicita(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="streamer", ricavi_attesi=45_000,
            natura_attivita=diagnosi.PROFESSIONALE,
        ))
        self.assertFalse(d.inquadramento_da_scegliere)
        self.assertEqual(d.gestione, previdenza.GESTIONE_SEPARATA)

    def test_natura_non_valida_rifiutata(self):
        with self.assertRaises(ValueError):
            diagnosi.Profilo(professione="streamer", ricavi_attesi=1_000, natura_attivita="altro")

    def test_costo_inquadramento_confronta_le_due_forme(self):
        d = diagnosi.analizza(diagnosi.Profilo(professione="streamer", ricavi_attesi=12_000))
        costo = d.costo_inquadramento
        self.assertIsNotNone(costo)
        self.assertAlmostEqual(
            costo["differenza"], costo["impresa"] - costo["professionale"], places=2
        )
        # A redditi bassi la quota fissa d'impresa pesa piu' della percentuale.
        self.assertGreater(costo["impresa"], costo["professionale"])

    def test_professioni_certe_non_chiedono_la_scelta(self):
        for slug in ("sviluppatore-software", "ecommerce"):
            d = diagnosi.analizza(diagnosi.Profilo(professione=slug, ricavi_attesi=45_000))
            self.assertFalse(d.inquadramento_da_scegliere, slug)
            self.assertIsNone(d.costo_inquadramento, slug)

    def test_ricavi_bassi_suggeriscono_la_prestazione_occasionale(self):
        d = diagnosi.analizza(diagnosi.Profilo(professione="copywriter", ricavi_attesi=3_000))
        self.assertTrue(any("partita IVA" in v.nome for v in d.verifiche))

    def test_investitore_cripto_avvisato_che_non_e_impresa(self):
        d = diagnosi.analizza(diagnosi.Profilo(professione="trader-cripto", ricavi_attesi=20_000))
        avviso = next(v for v in d.verifiche if "partita IVA" in v.nome)
        self.assertIn("33%", avviso.messaggio)

    def test_ecommerce_va_in_gestione_commercianti(self):
        d = diagnosi.analizza(diagnosi.Profilo(professione="ecommerce", ricavi_attesi=60_000))
        self.assertEqual(d.gestione, previdenza.COMMERCIANTI)
        self.assertTrue(any("Registro Imprese" in a.titolo for a in d.adempimenti))

    def test_riduzione_50_declassata_se_non_iscritto_nel_2025(self):
        d = diagnosi.analizza(
            diagnosi.Profilo(
                professione="ecommerce",
                ricavi_attesi=50_000,
                riduzione_richiesta=50,
                prima_iscrizione_2025=False,
            )
        )
        self.assertEqual(d.esito_forfettario.contributi.riduzione_applicata, 35)

    def test_tutte_le_professioni_producono_una_diagnosi(self):
        for p in professioni.CATALOGO:
            d = diagnosi.analizza(
                diagnosi.Profilo(professione=p.slug, ricavi_attesi=35_000),
                oggi=date(2026, 9, 6),
            )
            self.assertTrue(d.sintesi())
            self.assertGreaterEqual(d.esito_forfettario.totale_dovuto, 0)


class TestFormato(unittest.TestCase):
    def test_migliaia_e_decimali_all_italiana(self):
        self.assertEqual(formato.numero(7_860.11, 2), "7.860,11")
        self.assertEqual(formato.numero(122_295), "122.295")

    def test_numeri_piccoli_e_negativi(self):
        self.assertEqual(formato.numero(0), "0")
        self.assertEqual(formato.numero(-1_234.5, 2), "-1.234,50")

    def test_euro_e_percentuale(self):
        self.assertEqual(formato.euro(1_000), "1.000 euro")
        self.assertEqual(formato.percentuale(0.2607), "26,1%")
        self.assertEqual(formato.percentuale(0.15, 0), "15%")

    def test_messaggi_del_motore_non_usano_il_formato_inglese(self):
        # Regressione: i messaggi mostravano "7,860 euro" invece di "7.860 euro".
        d = diagnosi.analizza(diagnosi.Profilo(professione="ecommerce", ricavi_attesi=45_000))
        testo = " ".join([v.messaggio for v in d.verifiche] + list(d.avvisi))
        self.assertNotRegex(testo, r"\d,\d{3}")


class TestCripto(unittest.TestCase):
    def test_aliquota_ordinaria(self):
        e = cripto.calcola(10_000)
        self.assertAlmostEqual(e.imposta, 3_300.0, places=2)

    def test_moneta_elettronica_micar(self):
        e = cripto.calcola(10_000, moneta_elettronica=True)
        self.assertAlmostEqual(e.imposta, 2_600.0, places=2)

    def test_imposta_sul_valore(self):
        e = cripto.calcola(0, giacenza_media=50_000)
        self.assertAlmostEqual(e.imposta_valore, 100.0, places=2)
        self.assertAlmostEqual(e.totale_dovuto, 100.0, places=2)

    def test_nessuna_soglia_di_esenzione(self):
        self.assertGreater(cripto.calcola(50).imposta, 0)

    def test_minusvalenza_non_genera_imposta(self):
        self.assertEqual(cripto.calcola(-5_000).imposta, 0.0)


class TestDirittiAutore(unittest.TestCase):
    def test_abbattimento_ordinario(self):
        self.assertAlmostEqual(ordinario.reddito_diritti_autore(10_000), 7_500.0, places=2)

    def test_abbattimento_maggiorato_under_35(self):
        self.assertAlmostEqual(ordinario.reddito_diritti_autore(10_000, 30), 6_000.0, places=2)

    def test_a_35_anni_torna_ordinario(self):
        self.assertAlmostEqual(ordinario.reddito_diritti_autore(10_000, 35), 7_500.0, places=2)


class TestCostantiVive(unittest.TestCase):
    """Guard contro il ritorno di parametri dichiarati e mai usati."""

    def test_nessuna_costante_orfana(self):
        import pathlib
        import re

        radice = pathlib.Path(P.__file__).parent
        nomi = {
            n for n in dir(P)
            if n.isupper() and not n.startswith("_")
        }
        altrove = "\n".join(
            f.read_text()
            for f in radice.glob("*.py")
            if f.name != "parametri.py"
        )
        altrove += (radice.parent / "app_streamlit.py").read_text()
        orfane = {n for n in nomi if not re.search(rf"\b{n}\b", altrove)}
        self.assertEqual(orfane, set(), f"costanti dichiarate e mai usate: {sorted(orfane)}")


class TestMultiAttivita(unittest.TestCase):
    def componenti(self):
        return (
            forfettario.Componente("Sponsorizzazioni", 30_000, 0.78, "73.11.03"),
            forfettario.Componente("AdSense", 15_000, 0.67, "59.11.00"),
        )

    def test_coefficiente_medio_ponderato(self):
        atteso = (30_000 * 0.78 + 15_000 * 0.67) / 45_000
        self.assertAlmostEqual(forfettario.coefficiente_medio(self.componenti()), atteso, places=9)

    def test_media_produce_lo_stesso_reddito_dei_singoli(self):
        componenti = self.componenti()
        medio = forfettario.coefficiente_medio(componenti)
        self.assertAlmostEqual(
            sum(c.reddito for c in componenti),
            sum(c.ricavi for c in componenti) * medio,
            places=2,
        )

    def test_coefficiente_medio_una_sola_componente(self):
        solo = (forfettario.Componente("Unica", 10_000, 0.67),)
        self.assertAlmostEqual(forfettario.coefficiente_medio(solo), 0.67, places=9)

    def test_coefficiente_medio_senza_componenti(self):
        with self.assertRaises(ValueError):
            forfettario.coefficiente_medio(())

    def test_coefficiente_medio_ricavi_nulli(self):
        vuote = (forfettario.Componente("Nessun incasso", 0, 0.78),)
        self.assertEqual(forfettario.coefficiente_medio(vuote), 0.78)

    def test_componente_valida_gli_input(self):
        with self.assertRaises(ValueError):
            forfettario.Componente("x", -1, 0.78)
        with self.assertRaises(ValueError):
            forfettario.Componente("x", 100, 78)

    def test_diagnosi_applica_ogni_coefficiente_alla_sua_attivita(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="influencer",
            ricavi_attesi=30_000,
            altre_attivita=(diagnosi.AltraAttivita("youtuber", 15_000),),
        ))
        self.assertTrue(d.multi_attivita)
        self.assertAlmostEqual(
            d.esito_forfettario.reddito_forfetario,
            30_000 * 0.78 + 15_000 * 0.67,
            places=2,
        )

    def test_soglia_misurata_sulla_somma_dei_ricavi(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="ecommerce",
            ricavi_attesi=60_000,
            altre_attivita=(diagnosi.AltraAttivita("copywriter", 40_000),),
        ))
        self.assertEqual(d.ricavi_totali, 100_000)
        limite = next(v for v in d.verifiche if v.nome == "Limite dei ricavi")
        self.assertEqual(limite.esito, diagnosi.ATTENZIONE)

    def test_somma_oltre_100k_blocca(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="ecommerce",
            ricavi_attesi=60_000,
            altre_attivita=(diagnosi.AltraAttivita("copywriter", 50_000),),
        ))
        self.assertFalse(d.ammesso_al_forfettario)

    def test_gestione_segue_la_prevalente_non_la_dichiarata(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="copywriter",
            ricavi_attesi=5_000,
            altre_attivita=(diagnosi.AltraAttivita("ecommerce", 40_000),),
        ))
        self.assertEqual(d.gestione, previdenza.COMMERCIANTI)
        self.assertTrue(any(v.nome == "Attivita' prevalente" for v in d.verifiche))

    def test_prevalente_coincidente_non_genera_avviso(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="ecommerce",
            ricavi_attesi=40_000,
            altre_attivita=(diagnosi.AltraAttivita("copywriter", 5_000),),
        ))
        self.assertFalse(any(v.nome == "Attivita' prevalente" for v in d.verifiche))

    def test_nature_diverse_stimano_la_doppia_iscrizione(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="ecommerce",
            ricavi_attesi=40_000,
            altre_attivita=(diagnosi.AltraAttivita("copywriter", 10_000),),
        ))
        self.assertIsNotNone(d.contributi_doppia_iscrizione)
        atteso = (
            previdenza.gestione_separata(10_000 * 0.78).totale
            + previdenza.artigiani_commercianti(
                40_000 * 0.40, gestione=previdenza.COMMERCIANTI
            ).totale
        )
        self.assertAlmostEqual(d.contributi_doppia_iscrizione, atteso, places=2)
        self.assertTrue(any(v.nome == "Attivita' di natura diversa" for v in d.verifiche))

    def test_stessa_natura_non_genera_doppia_iscrizione(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="copywriter",
            ricavi_attesi=20_000,
            altre_attivita=(diagnosi.AltraAttivita("traduttore", 10_000),),
        ))
        self.assertIsNone(d.contributi_doppia_iscrizione)

    def test_attivita_singola_resta_invariata(self):
        d = diagnosi.analizza(diagnosi.Profilo(professione="copywriter", ricavi_attesi=30_000))
        self.assertFalse(d.multi_attivita)
        self.assertIsNone(d.contributi_doppia_iscrizione)
        self.assertAlmostEqual(d.coefficiente_medio, 0.78, places=9)

    def test_professione_ripetuta_rifiutata(self):
        with self.assertRaises(ValueError):
            diagnosi.Profilo(
                professione="copywriter",
                ricavi_attesi=10_000,
                altre_attivita=(diagnosi.AltraAttivita("copywriter", 5_000),),
            )

    def test_slug_sconosciuto_rifiutato_subito(self):
        with self.assertRaises(ValueError) as ctx:
            diagnosi.AltraAttivita("non-esiste", 1_000)
        self.assertIn("professione sconosciuta", str(ctx.exception))
        with self.assertRaises(ValueError):
            diagnosi.Profilo(professione="nemmeno-questa", ricavi_attesi=1_000)

    def test_altra_attivita_valida_i_ricavi(self):
        with self.assertRaises(ValueError):
            diagnosi.AltraAttivita("copywriter", -100)

    def test_natura_per_singola_attivita(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="streamer",
            ricavi_attesi=30_000,
            natura_attivita=diagnosi.IMPRESA,
            altre_attivita=(
                diagnosi.AltraAttivita("videomaker", 5_000, diagnosi.PROFESSIONALE),
            ),
        ))
        self.assertEqual(d.gestione, previdenza.COMMERCIANTI)
        self.assertFalse(d.inquadramento_da_scegliere)

    def test_sintesi_elenca_i_codici(self):
        d = diagnosi.analizza(diagnosi.Profilo(
            professione="influencer",
            ricavi_attesi=30_000,
            altre_attivita=(diagnosi.AltraAttivita("youtuber", 15_000),),
        ))
        self.assertIn("73.11.03", d.sintesi())
        self.assertIn("59.11.00", d.sintesi())


if __name__ == "__main__":
    unittest.main()
