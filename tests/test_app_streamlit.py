"""Smoke test dell'interfaccia Streamlit.

Esegue davvero lo script dell'app su piu' scenari e fallisce se solleva
eccezioni. Viene saltato dove Streamlit non e' installato, cosi' la suite del
motore resta eseguibile senza dipendenze.
"""

import pathlib
import unittest

try:
    from streamlit.testing.v1 import AppTest

    STREAMLIT_DISPONIBILE = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    STREAMLIT_DISPONIBILE = False

from fiscodigitale import professioni

APP = pathlib.Path(__file__).resolve().parent.parent / "app_streamlit.py"
TIMEOUT = 240


@unittest.skipUnless(STREAMLIT_DISPONIBILE, "Streamlit non installato")
class TestApp(unittest.TestCase):
    def avvia(self):
        return AppTest.from_file(str(APP), default_timeout=TIMEOUT).run()

    def assert_senza_eccezioni(self, at, contesto=""):
        self.assertEqual(
            list(at.exception), [], f"eccezione nell'app {contesto}: {at.exception}"
        )

    def test_avvio(self):
        at = self.avvia()
        self.assert_senza_eccezioni(at)
        self.assertTrue(at.title)

    def test_aliquota_startup_richiede_tutte_le_conferme(self):
        at = self.avvia()
        def casella(label):
            return next(c for c in at.sidebar.checkbox if c.label.startswith(label))
        self.assertFalse(casella("Sto avviando").value)
        casella("Sto avviando").set_value(True).run()
        self.assert_senza_eccezioni(at)
        casella("Nei tre anni").set_value(True)
        casella("Non e' mera").set_value(True)
        at.run()
        self.assertTrue(any("prudenziale al 15%" in x.value for x in at.markdown))
        casella("Non proseguo").set_value(True).run()
        self.assert_senza_eccezioni(at)
        self.assertFalse(any("prudenziale al 15%" in x.value for x in at.markdown))
        self.assertTrue(any("Requisiti dichiarati confermati" in x.value for x in at.markdown))

    def test_ecommerce_sospende_numeri_finche_manca_il_settore(self):
        at=self.avvia()
        next(x for x in at.sidebar.selectbox if x.label=="Professione").set_value(professioni.get("ecommerce")).run()
        self.assert_senza_eccezioni(at)
        self.assertNotIn("Netto annuo reale",[x.label for x in at.metric])
        next(x for x in at.sidebar.selectbox if x.key=="scenario_ateco_principale").set_value("47.71.10").run()
        self.assert_senza_eccezioni(at)
        self.assertIn("Netto annuo reale",[x.label for x in at.metric])

    def test_fpls_non_mostra_un_netto_forfettario(self):
        at=self.avvia()
        next(x for x in at.sidebar.radio if x.key=="verifica_fpls").set_value(True).run()
        self.assert_senza_eccezioni(at)
        self.assertFalse(at.metric)
        self.assertTrue(any("FPLS" in x.value for x in at.warning))

    def test_influencer_professionale_dopo_verifiche(self):
        at=self.avvia()
        at.sidebar.radio[0].set_value("professionale")
        next(x for x in at.sidebar.radio if x.key=="verifica_fpls").set_value(False)
        next(x for x in at.sidebar.checkbox if x.key=="verifica_specialistica").set_value(True)
        at.run()
        self.assert_senza_eccezioni(at)
        self.assertIn("Netto annuo reale",[x.label for x in at.metric])

    def test_prova_fcc_con_riduzione_2025(self):
        at = self.avvia()
        next(x for x in at.sidebar.selectbox if x.label == "Professione").set_value(professioni.get("ecommerce")).run()
        next(x for x in at.sidebar.selectbox if x.key == "scenario_ateco_principale").set_value("47.71.10")
        next(x for x in at.sidebar.checkbox if x.label == "Prima iscrizione INPS impresa nel 2025").set_value(True)
        at.run()
        next(x for x in at.sidebar.selectbox if x.label == "Riduzione contributiva richiesta").set_value(50).run()
        self.assert_senza_eccezioni(at)
        self.assertTrue(any("Piano sospeso" in x.value for x in at.info))
        self.assertEqual(at.tabs[0].label, "Il tuo risultato")
        self.assertTrue(any("Fisco Chiaro" in x.label for x in at.get("link_button")))

    def test_causa_di_esclusione(self):
        at = self.avvia()
        at.sidebar.number_input[4].set_value(50_000).run()  # redditi dipendente
        self.assert_senza_eccezioni(at, "con causa di esclusione")
        self.assertTrue(at.error)

    def test_ricavi_oltre_la_soglia(self):
        at = self.avvia()
        at.sidebar.number_input[0].set_value(150_000).run()
        self.assert_senza_eccezioni(at, "oltre i 100.000 euro")

    def test_scelta_inquadramento(self):
        at = self.avvia()
        at.sidebar.selectbox[1].set_value(professioni.get("streamer")).run()
        self.assert_senza_eccezioni(at, "su professione a inquadramento incerto")
        self.assertTrue(at.sidebar.radio, "manca la scelta della natura dell'attivita'")
        for natura in ("impresa", "professionale"):
            at.sidebar.radio[0].set_value(natura).run()
            self.assert_senza_eccezioni(at, f"con natura {natura}")

    def test_seconda_attivita(self):
        at = self.avvia()
        at.sidebar.multiselect[0].set_value([professioni.get("youtuber")]).run()
        self.assert_senza_eccezioni(at, "con una seconda attivita'")
        etichette = [m.label for m in at.metric]
        self.assertIn("Codici ATECO", etichette)


if __name__ == "__main__":
    unittest.main()

