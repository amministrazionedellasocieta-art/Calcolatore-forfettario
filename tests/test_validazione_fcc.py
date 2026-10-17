"""Casi di accettazione con risultati fissati da conteggi separati dal motore."""
from datetime import date
import unittest
from fiscodigitale import diagnosi as D, forfettario as F, previdenza as P, iva_estero as I, scadenze as S, contabilita as C, prova_fcc


class CasiCompleti(unittest.TestCase):
    def verifica(self, profilo, contributi, imposta, netto):
        d = D.analizza(profilo)
        self.assertTrue(d.stima_utilizzabile)
        self.assertEqual(d.esito_forfettario.contributi_dovuti, contributi)
        self.assertEqual(d.esito_forfettario.imposta_sostitutiva, imposta)
        self.assertEqual(d.netto_reale, netto)
        return d

    def test_professionista_con_servizi_esteri(self):
        # 31200 * 26,07% = 8133,84; (31200-8133,84)*15%=3459,92.
        self.verifica(D.Profilo('traduttore', 40000, costi_annui=2000,
            natura_attivita=D.PROFESSIONALE, acquisti_servizi_esteri=1000), 8133.84, 3459.92, 26186.24)

    def test_affiliate_impresa_confermato(self):
        # 4611,64 + (39000-18808)*24,48%=9554,64; imposta 4416,80.
        self.verifica(D.Profilo('affiliate-marketer', 50000, costi_annui=5000,
            natura_attivita=D.IMPRESA, verifica_specialistica_confermata=True), 9554.64, 4416.80, 31028.56)

    def test_ecommerce_abbigliamento(self):
        self.verifica(D.Profilo('ecommerce', 60000, costi_annui=20000,
            codice_ateco='47.71.10'), 5882.64, 2717.60, 31399.76)

    def test_due_attivita_professionali(self):
        # 20k traduzione e 20k marketing: entrambi coefficienti 78%, unica GS.
        self.verifica(D.Profilo('traduttore', 20000, costi_annui=2000,
            natura_attivita=D.PROFESSIONALE,
            altre_attivita=(D.AltraAttivita('social-media-manager', 20000, D.PROFESSIONALE),)),
            8133.84, 3459.92, 26406.24)

    def test_misto_non_esporta_netto_ipotetico(self):
        p = D.Profilo('traduttore', 20000, natura_attivita=D.PROFESSIONALE,
            altre_attivita=(D.AltraAttivita('ecommerce', 20000, codice_ateco='47.71.10'),))
        d = D.analizza(p)
        self.assertFalse(d.stima_utilizzabile)
        testo = prova_fcc.riepilogo(p, d)
        self.assertIn('STIMA SOSPESA', testo)
        self.assertNotIn('Contributi stimati:', testo)
        self.assertNotIn('Disponibile dopo costi', testo)


class Versamenti(unittest.TestCase):
    def test_riparto_isa(self):
        a = F.acconti(1000, soggetto_isa=True)
        self.assertEqual((a.prima_rata, a.seconda_rata), (500, 500))
        a = F.acconti(1000)
        self.assertEqual((a.prima_rata, a.seconda_rata), (400, 600))

    def test_proroga_2026_e_solo_perimetro_isa(self):
        for anno, isa, attesa in [(2026,True,date(2026,7,20)), (2026,False,date(2026,6,30)), (2027,True,date(2027,6,30))]:
            cal=S.calendario(anno,S.Profilo(soggetto_isa=isa))
            prima=next(x for x in cal if x.titolo=='Saldo imposte e primo acconto')
            self.assertEqual(prima.data,attesa)
        self.assertIn('0,80%',next(x for x in S.calendario(2026,S.Profilo(soggetto_isa=True)) if x.titolo=='Saldo imposte e primo acconto').descrizione)

    def test_festivi_agosto_e_oss(self):
        cal=S.calendario(2026,S.Profilo(acquisti_esteri=True,oss=True))
        iva=next(x for x in cal if x.data.month==8 and x.titolo=='Versamento IVA da inversione contabile')
        self.assertEqual(iva.data,date(2026,8,20))
        bollo=next(x for x in cal if x.titolo=='Imposta di bollo sulle fatture - terzo trimestre')
        self.assertEqual(bollo.data,date(2026,11,30))
        oss=next(x for x in cal if x.titolo=='Dichiarazione OSS - quarto trimestre')
        self.assertEqual(oss.data,date(2027,1,31))

    def test_intrastat_non_indovina_periodicita(self):
        for periodicita,n in [(None,0),('mensile',12),('trimestrale',4)]:
            cal=S.calendario(2026,S.Profilo(vendite_ue_b2b=True,periodicita_intrastat=periodicita))
            self.assertEqual(sum(x.titolo=='Elenchi INTRASTAT' for x in cal),n)

    def test_35_maternita_intera(self):
        c=P.artigiani_commercianti(0,gestione=P.ARTIGIANI,riduzione=35)
        self.assertEqual(c.totale,2941.49) # 4513,92*.65 + 7,44

    def test_50_indennizzo_intero_anche_eccedenza(self):
        c=P.artigiani_commercianti(30000,riduzione=50)
        # IVS 24% * 30000 / 2 + indennizzo .48% * 30000 + maternita.
        self.assertAlmostEqual(c.totale,3751.44,places=2)

    def test_scaglione_non_ragguagliato(self):
        c=P.artigiani_commercianti(40000,gestione=P.ARTIGIANI,mesi_attivita=6)
        self.assertEqual(c.quota_variabile,7343.04) # (40000-9404)*24%, sotto 56224 annui

    def test_50_non_esteso_oltre_i_36_mesi(self):
        with self.assertRaisesRegex(ValueError,'36 mesi'):
            F.piano_cassa(F.Situazione(30000,.4,gestione=P.COMMERCIANTI,riduzione=50))
        d=D.analizza(D.Profilo('ecommerce',30000,codice_ateco='47.71.10',riduzione_richiesta=50,prima_iscrizione_2025=True))
        self.assertEqual(d.piano_cassa,())


class Estero(unittest.TestCase):
    def test_oss_precedente_e_opzioni(self):
        for k in [dict(vendite_ue_b2c_anno_precedente=10001),dict(opzione_iva_destinazione=True),dict(stabilito_solo_italia=False),dict(importo=1001,vendite_ue_b2c_anno=9000)]:
            for oggetto in (I.BENE,I.SERVIZIO_ELETTRONICO):
                x=I.analizza(I.Operazione(oggetto=oggetto,area=I.UE,controparte=I.B2C,**k))
                self.assertIn('Paese del cliente',x.iva)

    def test_acquisti_ue_precedente_e_opzione(self):
        for k in [dict(acquisti_beni_ue_anno_precedente=10001),dict(opzione_acquisti_intracomunitari=True),dict(beni_speciali=True)]:
            x=I.analizza(I.Operazione(direzione=I.ACQUISTO,oggetto=I.BENE,area=I.UE,**k))
            self.assertIn('inversione contabile',x.iva)

    def test_servizi_esenti_o_speciali_sospesi(self):
        x=I.analizza(I.Operazione(direzione=I.ACQUISTO,servizio_generico_confermato=False))
        self.assertTrue(x.da_verificare)
        self.assertTrue(I.analizza_piattaforma('stripe')[1].da_verificare)
        self.assertTrue(I.analizza(I.Operazione(area=I.EXTRA_UE,controparte=I.B2C)).da_verificare)

    def test_oss_non_somma_servizi_generici(self):
        r=C.Registro(2026,[C.Movimento(date(2026,1,1),'consulenza',20000,area=I.UE,controparte=I.B2C)])
        self.assertEqual(r.vendite_ue_b2c,0)


class RegistroIva(unittest.TestCase):
    def test_precedente_sopra_soglia_e_opzione(self):
        m=C.Movimento(date(2026,1,1),'beni',1000,tipo=C.SPESA,area=I.UE,oggetto=I.BENE)
        for k in [dict(acquisti_beni_ue_precedenti=11000),dict(opzione_intracomunitari=True)]:
            self.assertEqual(C.Registro(2026,[m],**k).iva_reverse_charge_maturata,220)

    def test_commissione_esente(self):
        m=C.Movimento(date(2026,1,1),'pagamenti esenti verificati',1000,tipo=C.SPESA,area=I.UE,aliquota_iva=0)
        self.assertEqual(C.Registro(2026,[m]).iva_reverse_charge_maturata,0)

    def test_riepilogo_valido_inclusi_limiti(self):
        p=D.Profilo('traduttore',40000,natura_attivita=D.PROFESSIONALE)
        testo=prova_fcc.riepilogo(p,D.analizza(p))
        self.assertIn('Contributi stimati: 8133.84 EUR',testo)
        self.assertIn('non inviato automaticamente',testo)
