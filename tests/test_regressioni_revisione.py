"""Casi fiscali di regressione emersi dalla revisione della PR 2."""
import unittest
from datetime import date
from fiscodigitale import confronto, contabilita, diagnosi, forfettario, ordinario, previdenza


class TestRevisione(unittest.TestCase):
    def test_credito_compensato_non_ricompare_come_saldo(self):
        p = forfettario.piano_cassa(forfettario.Situazione(50000, .78), anni=5)
        self.assertEqual(p[2].imposta_cassa, 359.66)
        self.assertEqual(p[3].imposta_cassa, 5544.97)
        # Saldi delle annualita' chiuse + acconto dell'ultima annualita'.
        atteso = sum(a.imposta_competenza for a in p[:-1]) + p[-2].imposta_competenza
        self.assertAlmostEqual(sum(a.imposta_cassa for a in p), atteso, places=2)

    def test_fisso_inps_primo_anno_e_deduzione_per_cassa(self):
        p = forfettario.piano_cassa(forfettario.Situazione(20000, .4, gestione=previdenza.COMMERCIANTI))
        self.assertEqual(p[0].contributi_cassa, 3458.73)
        self.assertEqual(p[1].contributi_cassa, 4611.64)
        self.assertEqual(p[0].imposta_competenza, 681.19)

    def test_fisso_inps_apertura_luglio_e_anno_successivo_intero(self):
        p = forfettario.piano_cassa(forfettario.Situazione(10000, .4, gestione=previdenza.COMMERCIANTI, mesi_attivita=6))
        self.assertEqual(p[0].contributi_cassa, 1152.91)
        self.assertEqual(p[1].contributi_cassa, 4611.64)
        self.assertEqual(p[1].contributi_competenza, 4611.64)

    def test_iva_oltre_100000_non_e_retroattiva(self):
        e = forfettario.calcola(forfettario.Situazione(100001, .78))
        self.assertNotIn("tutte le operazioni", " ".join(e.avvisi))
        self.assertIn("superamento", " ".join(e.avvisi))
        r = contabilita.Registro(movimenti=[contabilita.Movimento(date(2026,1,1), 'Incasso',100001)])
        self.assertNotIn("gia' fatturate", " ".join(r.allerte()))

    def test_soglie_raggiunte_non_sono_superate(self):
        r = contabilita.Registro(movimenti=[contabilita.Movimento(date(2026,1,1), 'Incasso',85000)])
        self.assertNotIn('[SUPERATA]', ' '.join(r.allerte()))

    def test_confronto_include_iva_estera_e_modifica_pareggio(self):
        d = diagnosi.analizza(diagnosi.Profilo('copywriter',50000,costi_annui=10000,acquisti_servizi_esteri=10000))
        self.assertEqual(d.netto_reale, d.confronto_regimi.netto_forfettario)
        base = confronto.confronta(forfettario.Situazione(50000,.78),10000)
        self.assertEqual(round(base.netto_forfettario-d.confronto_regimi.netto_forfettario,2),2200)
        self.assertLess(d.confronto_regimi.costi_di_pareggio,base.costi_di_pareggio)

    def test_maggiorazione_detrazione_e_limiti(self):
        for reddito,bonus in [(11000,0),(11000.01,50),(15000,50),(17000,50),(17000.01,0)]:
            base = 500+765*(28000-reddito)/22500
            self.assertAlmostEqual(ordinario.detrazione_lavoro_autonomo(reddito),round(base+bonus,2),places=2)

    def test_startup_non_automatica(self):
        d = diagnosi.analizza(diagnosi.Profilo('copywriter',30000))
        self.assertEqual(d.esito_forfettario.aliquota,.15)
        d = diagnosi.analizza(diagnosi.Profilo('copywriter',30000,prima_attivita=True))
        self.assertEqual(d.esito_forfettario.aliquota,.15)
        self.assertTrue(any(v.nome=='Aliquota agevolata al 5%' and v.esito=='attenzione' for v in d.verifiche))

    def test_startup_solo_con_requisiti_confermati(self):
        d = diagnosi.analizza(diagnosi.Profilo('copywriter',30000,prima_attivita=True,requisiti_startup_confermati=True))
        self.assertEqual(d.esito_forfettario.aliquota,.05)

    def test_piano_startup_termina_dopo_cinque_periodi(self):
        p = forfettario.piano_cassa(forfettario.Situazione(50000,.78,startup=True),anni=6)
        self.assertEqual(p[5].imposta_competenza,4324.90)

    def test_iva_indetraibile_negativa_rifiutata(self):
        with self.assertRaises(ValueError):
            confronto.confronta(forfettario.Situazione(50000,.78),iva_indetraibile=-1)
