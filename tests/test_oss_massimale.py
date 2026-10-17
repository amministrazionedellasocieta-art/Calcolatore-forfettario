"""Scadenze OSS e massimale INPS: regressioni da fonti UE e INPS 14/2026."""
from datetime import date
import unittest
from fiscodigitale import scadenze, previdenza


class TestScadenzeOss(unittest.TestCase):
    def test_date_oss_2026_ultimo_giorno_del_mese(self):
        calendario=scadenze.calendario(2026,scadenze.Profilo(oss=True))
        date_oss=[s.data for s in calendario if s.titolo.startswith('Dichiarazione OSS')]
        self.assertEqual(date_oss,[date(2026,4,30),date(2026,7,31),date(2026,10,31),date(2027,1,31)])

    def test_oss_non_slitta_sabato_o_domenica(self):
        calendario=scadenze.calendario(2026,scadenze.Profilo(oss=True))
        oss={s.titolo:s.data for s in calendario if s.titolo.startswith('Dichiarazione OSS')}
        self.assertEqual(oss['Dichiarazione OSS - terzo trimestre'].weekday(),5)
        self.assertEqual(oss['Dichiarazione OSS - quarto trimestre'].weekday(),6)

    def test_prossime_oss_includono_31_gennaio_domenica(self):
        prossime=scadenze.prossime(10,da=date(2027,1,30),profilo=scadenze.Profilo(oss=True))
        oss=next(s for s in prossime if s.titolo.startswith('Dichiarazione OSS'))
        self.assertEqual(oss.data,date(2027,1,31))

    def test_scadenze_ordinarie_continuano_a_slittare(self):
        calendario=scadenze.calendario(2026,scadenze.Profilo(gestione=previdenza.COMMERCIANTI))
        prima=next(s for s in calendario if s.titolo=='Contributi INPS fissi - prima rata')
        self.assertEqual(prima.data,date(2026,5,18))


class TestMassimaleInps(unittest.TestCase):
    def test_massimale_non_taglia_reddito_oltre_61mila_con_sei_mesi(self):
        for gestione in (previdenza.ARTIGIANI,previdenza.COMMERCIANTI):
            a=previdenza.artigiani_commercianti(80000,gestione=gestione,mesi_attivita=6)
            b=previdenza.artigiani_commercianti(90000,gestione=gestione,mesi_attivita=6)
            # Entrambi oltre la prima fascia, entrambi sotto il massimale annuale.
            aliquota=.25 if gestione==previdenza.ARTIGIANI else .2548
            self.assertAlmostEqual(b.totale-a.totale,10000*aliquota,places=2)

    def test_tetto_annuale_vale_per_tutti_i_periodi(self):
        for mesi in (1,3,6,12):
            for gestione in (previdenza.ARTIGIANI,previdenza.COMMERCIANTI):
                with self.subTest(mesi=mesi,gestione=gestione):
                    sotto=previdenza.artigiani_commercianti(112295,gestione=gestione,mesi_attivita=mesi)
                    tetto=previdenza.artigiani_commercianti(122295,gestione=gestione,mesi_attivita=mesi)
                    sopra=previdenza.artigiani_commercianti(180000,gestione=gestione,mesi_attivita=mesi)
                    self.assertGreater(tetto.totale,sotto.totale)
                    self.assertEqual(tetto.totale,sopra.totale)

    def test_fisso_e_minimale_restano_ragguagliati(self):
        a=previdenza.artigiani_commercianti(0,mesi_attivita=6)
        b=previdenza.artigiani_commercianti(0,mesi_attivita=12)
        self.assertEqual(a.quota_fissa,2305.82)
        self.assertEqual(b.quota_fissa,4611.64)
