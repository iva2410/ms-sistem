from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, json, shutil
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io, base64

from baza import Session, Pacijent, Snimak, Pregled
from model_utils import (ucitaj_model, predvidi_sve_lezije,
                         predvidi_nove_lezije, izmeri_lezije)
from klinicki_sloj import klinicki_nalaz_nov_pacijent, klinicki_nalaz_kontrola

app = FastAPI(title='MS Sistem API')


def slika_preseka(snimak, maska):
    presek = int(np.argmax(np.sum(maska, axis=(0,1)))) if maska.sum()>0 else maska.shape[2]//2
    fig, ax = plt.subplots(figsize=(6,6))
    fig.patch.set_facecolor('white')
    ax.imshow(snimak[:,:,presek], cmap='gray')
    pm = maska[:,:,presek].astype(float)
    ax.imshow(np.ma.masked_where(pm==0, pm), cmap='autumn', alpha=0.7)
    ax.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=80)
    plt.close(fig)
    buf.seek(0)
    return 'data:image/png;base64,' + base64.b64encode(buf.read()).decode()

# dozvoli React (frontend) da pristupi
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://localhost:3000'],
    allow_methods=['*'], allow_headers=['*'],
)

# ucitaj modele jednom pri pokretanju
model_sve = ucitaj_model('modeli/model_gen.pt', in_channels=1)
model_nove = ucitaj_model('modeli/model_veci.pt', in_channels=2, channels=(32,64,128,256,320))

# folder za snimke
os.makedirs('snimci', exist_ok=True)

# ---------- PACIJENTI ----------
@app.post('/pacijent')
def dodaj_pacijenta(ime: str = Form(...), datum_rodjenja: str = Form('')):
    s = Session()
    p = Pacijent(ime=ime, datum_rodjenja=datum_rodjenja)
    s.add(p); s.commit()
    rezultat = {'id': p.id, 'ime': p.ime}
    s.close()
    return rezultat

@app.get('/pacijenti')
def svi_pacijenti():
    s = Session()
    lista = [{'id': p.id, 'ime': p.ime, 'datum_rodjenja': p.datum_rodjenja}
             for p in s.query(Pacijent).all()]
    s.close()
    return lista

@app.get('/pacijent/{pid}/istorija')
def istorija(pid: int):
    s = Session()
    pregledi = s.query(Pregled).filter_by(pacijent_id=pid).order_by(Pregled.datum.desc()).all()
    lista = [{'id': pr.id, 'tip': pr.tip, 'datum': pr.datum.strftime('%d.%m.%Y %H:%M'),
              'rezultati': json.loads(pr.rezultati)} for pr in pregledi]
    s.close()
    return lista

# ---------- PRVI PREGLED (sve lezije) ----------
@app.post('/analiza/prvi')
async def analiza_prvi(pacijent_id: int = Form(...), snimak: UploadFile = File(...)):
    s = Session()
    # sacuvaj snimak
    ime_fajla = f"snimci/p{pacijent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{snimak.filename}"
    with open(ime_fajla, 'wb') as f:
        shutil.copyfileobj(snimak.file, f)

    # analiza
    snimak_arr, maska = predvidi_sve_lezije(model_sve, ime_fajla)
    broj, ukupno, najveca, _ = izmeri_lezije(maska)
    nalaz = klinicki_nalaz_nov_pacijent(broj, ukupno, najveca, prosek_skupa=15.0)

    # sacuvaj u bazu
    snimak_zapis = Snimak(pacijent_id=pacijent_id, putanja=ime_fajla)
    s.add(snimak_zapis); s.commit()
    rezultati = {'broj_lezija': broj, 'zapremina_ml': round(ukupno/1000,2),
                 'najveca_ml': round(najveca/1000,2), 'nalaz': nalaz,
                 'slika': slika_preseka(snimak_arr, maska)}
    pregled = Pregled(pacijent_id=pacijent_id, snimak_id=snimak_zapis.id,
                      tip='prvi', rezultati=json.dumps(rezultati, ensure_ascii=False))
    s.add(pregled); s.commit()
    s.close()
    return rezultati

# ---------- KONTROLA (nove lezije) ----------
@app.post('/analiza/kontrola')
async def analiza_kontrola(pacijent_id: int = Form(...), snimak: UploadFile = File(...)):
    s = Session()
    # nadji PRETHODNI snimak pacijenta
    prethodni = s.query(Snimak).filter_by(pacijent_id=pacijent_id).order_by(Snimak.datum.desc()).first()
    if prethodni is None:
        s.close()
        raise HTTPException(status_code=400,
                            detail='Nema prethodnog snimka. Prvo uradite prvi pregled.')

    # sacuvaj NOVI snimak
    ime_fajla = f"snimci/p{pacijent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{snimak.filename}"
    with open(ime_fajla, 'wb') as f:
        shutil.copyfileobj(snimak.file, f)

    # uporedi prethodni (raniji) i novi
    _, s2_arr, nove = predvidi_nove_lezije(model_nove, prethodni.putanja, ime_fajla)
    broj, ukupno, najveca, _ = izmeri_lezije(nove)
    nalaz = klinicki_nalaz_kontrola(broj, ukupno)

    # sacuvaj u bazu
    snimak_zapis = Snimak(pacijent_id=pacijent_id, putanja=ime_fajla)
    s.add(snimak_zapis); s.commit()
    rezultati = {'broj_novih_lezija': broj, 'zapremina_novih_ml': round(ukupno/1000,2),
                 'nalaz': nalaz, 'slika': slika_preseka(s2_arr, nove)}
    pregled = Pregled(pacijent_id=pacijent_id, snimak_id=snimak_zapis.id,
                      tip='kontrola', rezultati=json.dumps(rezultati, ensure_ascii=False))
    s.add(pregled); s.commit()
    s.close()
    return rezultati