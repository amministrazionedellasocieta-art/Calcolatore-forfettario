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
