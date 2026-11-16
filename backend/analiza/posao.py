"""Izvrsavanje analiza u pozadini (jedna po jedna, da racunar ostane upotrebljiv)."""
import json
import queue
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np

import konfiguracija as kfg
from analiza import merenja, motor, prikaz, registracija
from baza import Analiza, Pregled, Sesija

_red = queue.Queue()
_nit = None

DODATNE_SEKVENCE = ('STIR', 'PSIR', 'MP2RAGE')


def kes_snimka(snimak_id):
    return kfg.PRIKAZ / 'snimak_{}.npy'.format(snimak_id)


def dodaj(analiza_id):
    _red.put(analiza_id)
    _pokreni_nit()


def _pokreni_nit():
    global _nit
    if _nit is None or not _nit.is_alive():
        _nit = threading.Thread(target=_petlja, name='ms-analize', daemon=True)
        _nit.start()


def nastavi_prekinute():
    """Posle restarta servera: analize koje nisu zavrsene vracaju se u red."""
    s = Sesija()
    try:
        for a in s.query(Analiza).filter(Analiza.status.in_(('na_cekanju', 'u_toku'))).order_by(Analiza.id):
            a.status, a.korak, a.napredak = 'na_cekanju', 'Čeka na red', 0
            s.commit()
            dodaj(a.id)
    finally:
        s.close()


def _petlja():
    while True:
        analiza_id = _red.get()
        try:
            _obradi(analiza_id)
        except Exception:
            traceback.print_exc()
        finally:
            _red.task_done()


def _stanje(s, a, korak, napredak):
    a.status, a.korak, a.napredak = 'u_toku', korak, napredak
    s.commit()


def _snimak(pregled, *sekvence):
    for sn in pregled.snimci:
        if sn.sekvenca in sekvence:
            return sn
    return None


def _obradi(analiza_id):
    s = Sesija()
    pocetak = time.time()
    try:
        a = s.get(Analiza, analiza_id)
        if a is None or a.status == 'zavrsena':
            return
        pregled = a.pregled
        folder = kfg.ANALIZE / 'analiza_{}'.format(a.id)
        folder.mkdir(parents=True, exist_ok=True)
        a.folder, a.greska = str(folder), ''
        _stanje(s, a, 'Priprema snimaka', 5)

        if a.tip == 'sve_lezije':
            rezultati = _sve_lezije(s, a, pregled, folder)
        elif a.tip == 'nove_lezije':
            rezultati = _nove_lezije(s, a, pregled, folder)
        else:
            raise RuntimeError('Nepoznat tip analize: {}'.format(a.tip))

        a.rezultati = json.dumps(rezultati, ensure_ascii=False)
        a.model = rezultati['tehnika']['model']
        a.status, a.korak, a.napredak = 'zavrsena', 'Završeno', 100
        a.zavrsena, a.trajanje_s = datetime.now(), round(time.time() - pocetak, 1)
        s.commit()
    except Exception as e:
        s.rollback()
        a = s.get(Analiza, analiza_id)
        if a is not None:
            a.status, a.korak, a.greska = 'greska', 'Greška', str(e)
            a.trajanje_s = round(time.time() - pocetak, 1)
            s.commit()
        traceback.print_exc()
    finally:
        s.close()


def _izmeri_i_sacuvaj(folder, maska_p, verov_p, razmak):
    """Maska i verovatnoca -> standardna orijentacija, merenje, slojevi za prikaz."""
    sirova = folder / '_maska_sirova.npy'
    prikaz.pripremi_sloj(maska_p, sirova)
    prikaz.pripremi_sloj(verov_p, folder / 'verovatnoca.npy')
    maska = np.load(sirova)
    verov = np.load(folder / 'verovatnoca.npy')
    sazetak, cista = merenja.izmeri(maska, verov, razmak)
    np.save(folder / 'maska.npy', cista)
    sirova.unlink(missing_ok=True)
    return sazetak


def _sve_lezije(s, a, pregled, folder):
    tehnika = {}
    if pregled.region == 'mozak':
        glavni = _snimak(pregled, 'FLAIR')
        if glavni is None:
            raise RuntimeError('Pregled nema FLAIR snimak.')
        kljuc, kanali = 'mozak_sve', [glavni.putanja]
        tehnika['ulaz'] = 'FLAIR'
    else:
        glavni = _snimak(pregled, 'T2')
        if glavni is None:
            raise RuntimeError('Pregled nema T2 snimak.')
        dodatna = _snimak(pregled, *DODATNE_SEKVENCE)
        if dodatna is None:
            raise RuntimeError('Pregled nema drugu sekvencu (STIR, PSIR ili MP2RAGE).')
        _stanje(s, a, 'Poravnanje druge sekvence sa T2', 15)
        na_mrezi = folder / 'dodatna_na_t2.nii.gz'
        tehnika['registracija'] = registracija.dodatna_na_t2(
            glavni.putanja, dodatna.putanja, na_mrezi, kfg.KICMA_REGISTRACIJA)
        kljuc, kanali = 'kicma', [glavni.putanja, str(na_mrezi)]
        tehnika['ulaz'] = 'T2 + ' + dodatna.sekvenca

    meta = prikaz.pripremi_snimak(glavni.putanja, kes_snimka(glavni.id))
    _stanje(s, a, 'Segmentacija lezija', 30)
    maska_p, verov_p, info = motor.segmentuj(kljuc, kanali, folder)
    tehnika.update(info)
    _stanje(s, a, 'Merenje lezija', 90)
    sazetak = _izmeri_i_sacuvaj(folder, maska_p, verov_p, meta['razmak'])
    sazetak.update(tehnika=tehnika, snimak_id=glavni.id, oblik=meta['oblik'], razmak=meta['razmak'])
    return sazetak


def _nove_lezije(s, a, pregled, folder):
    noviji = _snimak(pregled, 'FLAIR')
    prethodni = s.get(Pregled, a.prethodni_pregled_id) if a.prethodni_pregled_id else None
    raniji = _snimak(prethodni, 'FLAIR') if prethodni else None
    if noviji is None or raniji is None:
        raise RuntimeError('Za poređenje su potrebna dva FLAIR snimka (raniji i noviji).')

    meta = prikaz.pripremi_snimak(noviji.putanja, kes_snimka(noviji.id))
    _stanje(s, a, 'Poravnanje ranijeg snimka sa novijim', 15)
    raniji_p = folder / 'raniji_poravnat.nii.gz'
    reg = registracija.poravnaj_vremenske_tacke(noviji.putanja, raniji.putanja, raniji_p)
    prikaz.pripremi_snimak(raniji_p, folder / 'raniji.npy')

    _stanje(s, a, 'Detekcija novih lezija', 35)
    maska_p, verov_p, info = motor.segmentuj('mozak_nove', [str(raniji_p), noviji.putanja], folder)
    _stanje(s, a, 'Merenje lezija', 90)
    sazetak = _izmeri_i_sacuvaj(folder, maska_p, verov_p, meta['razmak'])
    tehnika = dict(info, ulaz='FLAIR (raniji) + FLAIR (noviji)', registracija=reg)
    sazetak.update(tehnika=tehnika, snimak_id=noviji.id, oblik=meta['oblik'], razmak=meta['razmak'],
                   prethodni_pregled_id=prethodni.id,
                   prethodni_datum=prethodni.datum_snimanja.isoformat())
    return sazetak
