"""Podesavanja aplikacije. Vrednosti se citaju iz okruzenja ili iz fajla backend/.env."""
import os
import secrets
from pathlib import Path

KOREN = Path(__file__).resolve().parent


def _ucitaj_env():
    putanja = KOREN / '.env'
    if not putanja.exists():
        return
    for red in putanja.read_text(encoding='utf-8').splitlines():
        red = red.strip()
        if not red or red.startswith('#') or '=' not in red:
            continue
        kljuc, vrednost = red.split('=', 1)
        os.environ.setdefault(kljuc.strip(), vrednost.strip().strip('"').strip("'"))

_ucitaj_env()

# --- baza ---
BAZA_URL = os.environ.get(
    'MS_BAZA_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/ms_sistem')

# --- folderi ---
PODACI = Path(os.environ.get('MS_PODACI', KOREN / 'podaci'))
SNIMCI = PODACI / 'snimci'
ANALIZE = PODACI / 'analize'
PRIKAZ = PODACI / 'prikaz'
MODELI = Path(os.environ.get('MS_MODELI', KOREN / 'modeli'))
for _f in (SNIMCI, ANALIZE, PRIKAZ, MODELI):
    _f.mkdir(parents=True, exist_ok=True)

# --- prijava ---
TRAJANJE_PRIJAVE_H = int(os.environ.get('MS_TRAJANJE_PRIJAVE_H', '12'))


def tajni_kljuc() -> str:
    """Kljuc za potpisivanje prijava. Ako nije zadat, pravi se jednom i cuva u podaci/.tajna."""
    if os.environ.get('MS_TAJNI_KLJUC'):
        return os.environ['MS_TAJNI_KLJUC']
    fajl = PODACI / '.tajna'
    if not fajl.exists():
        fajl.write_text(secrets.token_hex(32), encoding='utf-8')
    return fajl.read_text(encoding='utf-8').strip()


# --- frontend adrese kojima je dozvoljen pristup ---
DOZVOLJENI_IZVORI = [a.strip() for a in os.environ.get(
    'MS_DOZVOLJENI_IZVORI', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if a.strip()]

# --- modeli (nnU-Net folderi unutar backend/modeli) ---
# kljuc -> (naziv foldera skupa, opis za prikaz, broj ulaznih kanala)
KICMA_MULTI = os.environ.get('MS_KICMA_MULTI', 'Dataset013_SpineNOREG')
MODELI_REGISTAR = {
    'mozak_sve':   ('Dataset001_MsBrain',  'Mozak, sve lezije (FLAIR)', 1),
    'mozak_nove':  ('Dataset021_BrainNew', 'Mozak, nove lezije (dva FLAIR snimka)', 2),
    'kicma':       (KICMA_MULTI,           'Kičmena moždina (T2 + STIR / PSIR / MP2RAGE)', 2),
}

# registracija dodatne sekvence na T2 kod kicme: 'zasticena' (primeni samo ako popravlja) ili 'bez'
KICMA_REGISTRACIJA = os.environ.get('MS_KICMA_REGISTRACIJA', 'zasticena')

# 'auto' -> GPU ako postoji, inace CPU
UREDJAJ = os.environ.get('MS_UREDJAJ', 'auto')

# pragovi za kategoriju pouzdanosti detekcije (srednja vrednost izlaza modela unutar lezije)
PRAG_POUZDANOST_VISOKA = float(os.environ.get('MS_PRAG_VISOKA', '0.85'))
PRAG_POUZDANOST_SREDNJA = float(os.environ.get('MS_PRAG_SREDNJA', '0.65'))
# najmanja lezija koja se prijavljuje (u vokselima), manje se smatra sumom
MIN_VOKSELA = int(os.environ.get('MS_MIN_VOKSELA', '3'))
