"""Regressioni su struttura ISTAT e inquadramenti che non sono automatici."""
import json
from pathlib import Path
import unittest
from fiscodigitale import professioni,diagnosi,previdenza

class TestCatalogoVerificato(unittest.TestCase):
    def test_tutte_le_44_schede_hanno_evidenza(self):
        dati=json.loads((Path(professioni.__file__).with_name('catalogo_verifiche.json')).read_text())
        self.assertEqual(len(dati['attivita']),44)
        for p in professioni.CATALOGO:
            self.assertIn(p.slug,dati['attivita'])
            for code in p.codici_scenario:
                self.assertIn(code,dati['codici'])
            if p.ateco:
                self.assertEqual(p.ateco_descrizione,dati['codici'][p.ateco]['titolo'])

    def test_codici_corretti_da_struttura_istat(self):
        attesi={'podcaster':'59.20.10','fotografo':'74.20.19','musicista-digitale':'90.11.09',
                'scrittore-self':'58.11.00','consulente-it':'62.20.10','cybersecurity':'62.20.10',
                'no-code':'62.20.10','digital-strategist':'70.20.09','virtual-assistant':'82.10.00',
                'nft-artist':'90.12.00','formatore-online':'85.59.20','tutor-online':'85.59.99'}
        for slug,code in attesi.items():
            self.assertEqual(professioni.get(slug).ateco,code)

    def test_ecommerce_non_riusa_il_codice_di_intermediazione_usato(self):
        for slug in ['ecommerce','dropshipping','amazon-fba','print-on-demand']:
            p=professioni.get(slug)
            self.assertEqual(p.ateco,'')
            self.assertNotIn('47.91.10',p.codici_scenario)
        d=diagnosi.analizza(diagnosi.Profilo('ecommerce',40000))
        self.assertFalse(d.stima_utilizzabile)
        self.assertNotIn("Non e' un'attivita' con partita IVA",[v.nome for v in d.verifiche])
        d=diagnosi.analizza(diagnosi.Profilo('ecommerce',40000,codice_ateco='47.71.10'))
        self.assertTrue(d.stima_utilizzabile)
        self.assertEqual(d.esito_forfettario.coefficiente,.4)
        self.assertEqual(d.gestione,previdenza.COMMERCIANTI)

    def test_corso_non_e_automaticamente_edizione_software(self):
        self.assertEqual(professioni.get('infoprodotti').ateco,'')
        corso=diagnosi.analizza(diagnosi.Profilo('infoprodotti',40000,codice_ateco='85.59.20',natura_attivita=diagnosi.PROFESSIONALE))
        ebook=diagnosi.analizza(diagnosi.Profilo('infoprodotti',40000,codice_ateco='58.11.00',natura_attivita=diagnosi.IMPRESA))
        self.assertEqual(corso.esito_forfettario.coefficiente,.78)
        self.assertEqual(ebook.esito_forfettario.coefficiente,.67)

    def test_scenario_secondario_modifica_il_coefficiente_ponderato(self):
        d=diagnosi.analizza(diagnosi.Profilo('copywriter',30000,altre_attivita=(diagnosi.AltraAttivita('infoprodotti',10000,diagnosi.PROFESSIONALE,'58.11.00'),)))
        self.assertEqual(d.attivita[1].professione.ateco,'58.11.00')
        self.assertAlmostEqual(d.esito_forfettario.reddito_forfetario,30100,places=2)

    def test_codice_estraneo_rifiutato(self):
        with self.assertRaises(ValueError):
            professioni.con_codice('ecommerce','73.11.03')

    def test_fpls_non_viene_simulato_in_gestione_separata(self):
        with self.assertRaisesRegex(ValueError,'FPLS'):
            diagnosi.analizza(diagnosi.Profilo('influencer',30000,prestazioni_spettacolo=True))
        d=diagnosi.analizza(diagnosi.Profilo('influencer',30000,natura_attivita=diagnosi.PROFESSIONALE))
        self.assertFalse(d.stima_utilizzabile)
        d=diagnosi.analizza(diagnosi.Profilo('influencer',30000,natura_attivita=diagnosi.PROFESSIONALE,prestazioni_spettacolo=False,verifica_specialistica_confermata=True))
        self.assertTrue(d.stima_utilizzabile)
        self.assertEqual(d.gestione,previdenza.GESTIONE_SEPARATA)

    def test_camera_commercio_segue_la_natura_scelta(self):
        professionale=diagnosi.analizza(diagnosi.Profilo('streamer',30000,natura_attivita=diagnosi.PROFESSIONALE,prestazioni_spettacolo=False))
        impresa=diagnosi.analizza(diagnosi.Profilo('streamer',30000,natura_attivita=diagnosi.IMPRESA,prestazioni_spettacolo=False))
        self.assertFalse(any(a.titolo=='Iscrizione al Registro Imprese e SCIA' for a in professionale.adempimenti))
        self.assertTrue(any(a.titolo=='Iscrizione al Registro Imprese e SCIA' for a in impresa.adempimenti))

    def test_attivita_miste_non_scelgono_inps_solo_per_ricavi(self):
        d=diagnosi.analizza(diagnosi.Profilo('copywriter',10000,altre_attivita=(diagnosi.AltraAttivita('ecommerce',40000,codice_ateco='47.71.10'),)))
        self.assertFalse(d.stima_utilizzabile)
        self.assertTrue(any(v.nome=='Previdenza da verificare' for v in d.verifiche))

    def test_print_on_demand_design_non_viene_trattato_da_commerciante(self):
        p=professioni.con_codice('print-on-demand','74.12.09')
        self.assertEqual(p.coefficiente,.78)
        self.assertEqual(p.gestione_inps,professioni.DIPENDE)

    def test_tutti_gli_scenari_del_catalogo_si_risolvono(self):
        for p in professioni.CATALOGO:
            for code in p.codici_scenario:
                with self.subTest(slug=p.slug,code=code):
                    d=diagnosi.analizza(diagnosi.Profilo(p.slug,30000,codice_ateco=code))
                    self.assertEqual(d.professione.ateco,code)
                    self.assertEqual(d.attivita[0].componente.coefficiente,d.professione.coefficiente)

    def test_servizi_professionali_non_impongono_la_gestione_senza_natura(self):
        for slug in ['sviluppatore-software','copywriter','consulente-it','social-media-manager']:
            d=diagnosi.analizza(diagnosi.Profilo(slug,30000))
            self.assertTrue(d.inquadramento_da_scegliere)
            self.assertFalse(d.stima_utilizzabile)
            d=diagnosi.analizza(diagnosi.Profilo(slug,30000,natura_attivita=diagnosi.PROFESSIONALE))
            self.assertTrue(d.stima_utilizzabile)
