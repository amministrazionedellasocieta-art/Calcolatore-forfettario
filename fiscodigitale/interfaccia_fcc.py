"""Aspetto FCC; nessuna dipendenza dai calcoli fiscali."""
import base64
from pathlib import Path

import streamlit as st

LOGO = Path(__file__).resolve().parent.parent / 'assets' / 'fcc-logo-original.webp'


def applica():
    st.markdown('''<style>
:root { --fcc-navy:#0a1628; --fcc-teal:#147f7b; --fcc-gold:#d4a843; }
.stApp { background:#f8f6f1; color:#14243a; }
[data-testid="stMainBlockContainer"] { max-width:1240px; padding-top:2rem; padding-bottom:3rem; }
[data-testid="stHeader"] { background:#f8f6f1; }
[data-testid="stToolbar"] { display:none; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e5e7eb; }
[data-testid="stSidebar"] h1 { font-size:1.3rem; }
h1 { color:#0a1628; letter-spacing:-.035em; font-weight:750; }
h2,h3 { color:#14243a; letter-spacing:-.02em; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e0e5e9; border-top:3px solid #147f7b; border-radius:16px; padding:20px; min-height:140px; }
[data-testid="stMetricLabel"] { color:#4f5d70; }
[data-testid="stMetricValue"] { color:#0a1628; font-size:2rem; font-weight:650; }
[role="tablist"] { gap:8px; padding:4px 0 10px; overflow-x:auto; }
button[role="tab"] { background:#fff; border:1px solid #dce2e9; border-radius:30px; padding:10px 17px; height:auto; white-space:nowrap; }
button[role="tab"][aria-selected="true"] { background:#0a1628; color:#fff; border-color:#0a1628; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none; }
[data-testid="stLinkButton"] a[kind="primary"] { background:#147f7b; border-color:#147f7b; border-radius:10px; font-weight:600; min-height:46px; }
[data-testid="stDownloadButton"] button { border-radius:10px; min-height:46px; }
[data-testid="stExpander"] { background:#fff; border-radius:12px; }
[data-testid="stAlert"] { border-radius:12px; }
.fcc-brand { display:flex; align-items:center; gap:20px; margin-bottom:24px; }
.fcc-brand img { width:110px; height:auto; border-radius:8px; }
.fcc-brand-name { color:#0a1628; font-size:16px; font-weight:700; }
.fcc-brand-note { color:#667385; font-size:13px; margin-top:4px; }
.fcc-badge { margin-left:auto; font-size:12px; color:#80621e; background:#fff4d9; border:1px solid #e8d7a7; padding:7px 12px; border-radius:20px; white-space:nowrap; }
.fcc-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:16px 0 24px; }
.fcc-step { background:#fff; border:1px solid #dce2e9; border-radius:12px; padding:14px 16px; font-size:14px; }
.fcc-step b { color:#147f7b; margin-right:8px; }
.fcc-mobile-help { display:none; }
.fcc-next { border-left:3px solid #d4a843; padding:3px 0 3px 16px; margin:22px 0 12px; }
.fcc-next strong { color:#0a1628; font-size:19px; }
.fcc-next p { color:#4f5d70; margin:6px 0; font-size:15px; }
@media(max-width:740px) {
 [data-testid="stMainBlockContainer"] { padding:1rem 1rem 2rem; }
 h1 { font-size:1.9rem !important; line-height:1.15 !important; }
 .fcc-brand { gap:12px; margin:18px 0; flex-wrap:wrap; }
 .fcc-brand img { width:84px; }
 .fcc-brand-name { font-size:14px; }
 .fcc-brand-note { font-size:12px; }
 .fcc-badge { display:none; }
 .fcc-steps { gap:6px; }
 .fcc-step { font-size:12px; padding:10px 8px; }
 .fcc-step b { display:block; margin-bottom:3px; }
 .fcc-mobile-help { display:block; background:#eaf4f2; padding:12px 14px; border-radius:10px; font-size:14px; color:#155b58; margin:12px 0; }
 [data-testid="stMetric"] { padding:16px 18px; min-height:108px; }
 [data-testid="stLinkButton"] a, [data-testid="stDownloadButton"] button { width:100%; }
}
</style>''', unsafe_allow_html=True)


def testata():
    logo = base64.b64encode(LOGO.read_bytes()).decode()
    st.markdown(f'''<div class="fcc-brand"><img src="data:image/webp;base64,{logo}" alt="Logo Fisco Chiaro">
<div><div class="fcc-brand-name">Fisco Chiaro Consulting</div><div class="fcc-brand-note">Il metodo dello Studio. Anche nei tuoi numeri.</div></div>
<span class="fcc-badge">Versione di prova · 2026</span></div>''', unsafe_allow_html=True)
    st.title('La tua attività, in chiaro.')
    st.write('Una prima stima per orientarti. Un confronto con lo Studio per decidere.')
    st.markdown('''<div class="fcc-steps"><div class="fcc-step"><b>01</b>Racconta la tua attività</div><div class="fcc-step"><b>02</b>Leggi la tua stima</div><div class="fcc-step"><b>03</b>Confrontati con lo Studio</div></div>
<div class="fcc-mobile-help">Per iniziare, apri il profilo dal menu in alto a sinistra e inserisci i tuoi dati.</div>''', unsafe_allow_html=True)
