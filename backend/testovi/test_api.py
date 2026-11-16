"""Testovi API-ja. Pokretanje iz foldera backend:  python -m pytest testovi -q
Koriste privremenu SQLite bazu i zamenu za model (ne traze GPU ni instalirane modele)."""
import os
import sys
import tempfile
import time
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix='ms_test_'))
os.environ['MS_BAZA_URL'] = 'sqlite:///{}'.format(_tmp / 'test.db')
os.environ['MS_PODACI'] = str(_tmp / 'podaci')
os.environ['MS_MODELI'] = str(_tmp / 'modeli')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from fastapi.testclient import TestClient

from analiza import motor
from fantom import fantom, lazni_model
from main import app


@pytest.fixture(scope='module')
def klijent():
    motor.segmentuj = lazni_model
    with TestClient(app) as k:
        yield k


@pytest.fixture(scope='module')
def zaglavlje(klijent):
    r = klijent.post('/nalog/registracija', json={
        'email': 'Lekar@Primer.rs', 'lozinka': 'duga-lozinka-1', 'ime': 'Ana', 'prezime': 'Anić',
        'titula': 'dr', 'specijalnost': 'radiologija', 'ustanova': 'Klinički centar', 'broj_licence': '12345'})
    assert r.status_code == 200, r.text
    return {'Authorization': 'Bearer ' + r.json()['token']}


def _cekaj(klijent, zaglavlje, pid, sekundi=120):
    for _ in range(sekundi * 4):
        p = klijent.get('/pregledi/{}'.format(pid), headers=zaglavlje).json()
        if all(a['status'] in ('zavrsena', 'greska') for a in p['analize'].values()):
            return p
        time.sleep(0.25)
    raise AssertionError('analiza nije završena na vreme')


def test_nalog(klijent, zaglavlje):
    assert klijent.get('/pacijenti').status_code == 401
    assert klijent.post('/nalog/registracija', json={
        'email': 'lekar@primer.rs', 'lozinka': 'duga-lozinka-1', 'ime': 'A', 'prezime': 'B'}).status_code == 409
    assert klijent.post('/nalog/registracija', json={
        'email': 'x@y.rs', 'lozinka': 'kratka', 'ime': 'A', 'prezime': 'B'}).status_code == 422
    assert klijent.post('/nalog/prijava', json={'email': 'lekar@primer.rs', 'lozinka': 'pogresna'}).status_code == 401
    r = klijent.post('/nalog/prijava', json={'email': 'LEKAR@primer.rs', 'lozinka': 'duga-lozinka-1'})
    assert r.status_code == 200 and r.json()['lekar']['puno_ime'] == 'dr Ana Anić'
    assert klijent.get('/nalog/ja', headers={'Authorization': 'Bearer nevazeci'}).status_code == 401


def test_mozak_prvi_i_kontrolni(klijent, zaglavlje, tmp_path):
    r = klijent.post('/pacijenti', headers=zaglavlje, json={
        'ime': 'Petar', 'prezime': 'Petrović', 'broj_kartona': 'K-100', 'datum_rodjenja': '1985-03-15', 'pol': 'M'})
    pac = r.json()['id']
    assert klijent.get('/pacijenti?pretraga=petro', headers=zaglavlje).json()[0]['id'] == pac
    assert klijent.get('/pacijenti?pretraga=nema', headers=zaglavlje).json() == []

    stare = [(20, 30, 25, 3), (42, 40, 30, 2)]
    fantom(tmp_path / 'a.nii.gz', stare)
    with open(tmp_path / 'a.nii.gz', 'rb') as f:
        r = klijent.post('/pregledi', headers=zaglavlje, files={'flair': ('a.nii.gz', f)},
                         data={'pacijent_id': pac, 'region': 'mozak', 'datum_snimanja': '2025-01-10'})
    assert r.status_code == 200, r.text
    p1 = _cekaj(klijent, zaglavlje, r.json()['id'])
    sve = p1['analize']['sve_lezije']
    assert sve['status'] == 'zavrsena', sve
    assert sve['rezultati']['broj_lezija'] == 2
    assert 'nove_lezije' not in p1['analize']
    najveca = sve['rezultati']['lezije'][0]
    assert abs(najveca['zapremina_mm3'] - 4 / 3 * 3.14159 * 27 * 1.2) < 40     # kugla r=3, voksel 1.2 mm3
    assert najveca['kategorija'] == 'visoka'

    # kontrolni: pacijent pomeren 2 voksela, jedna nova lezija
    fantom(tmp_path / 'b.nii.gz', stare + [(30, 50, 22, 3)], pomeraj=(2, -1, 0), seme=1)
    with open(tmp_path / 'b.nii.gz', 'rb') as f:
        r = klijent.post('/pregledi', headers=zaglavlje, files={'flair': ('b.nii.gz', f)},
                         data={'pacijent_id': pac, 'region': 'mozak', 'datum_snimanja': '2025-07-10'})
    p2 = _cekaj(klijent, zaglavlje, r.json()['id'])
    nove = p2['analize']['nove_lezije']
    assert nove['status'] == 'zavrsena', nove
    assert nove['rezultati']['tehnika']['registracija']['primenjena'] is True
    assert nove['rezultati']['broj_lezija'] == 1, nove['rezultati']       # registracija uklanja lazne 'nove'
    assert p2['analize']['sve_lezije']['rezultati']['broj_lezija'] == 3
    assert p2['prethodni']['id'] == p1['id']

    # preseci i slojevi
    sid = p2['snimci'][0]['id']
    for ravan in ('aksijalni', 'koronalni', 'sagitalni'):
        r = klijent.get('/snimci/{}/presek?ravan={}&i=20'.format(sid, ravan), headers=zaglavlje)
        assert r.status_code == 200 and r.content[:4] == b'\x89PNG'
    for vrsta in ('lezije', 'pouzdanost'):
        assert klijent.get('/analize/{}/sloj?vrsta={}&i=22'.format(nove['id'], vrsta), headers=zaglavlje).status_code == 200
    assert klijent.get('/analize/{}/raniji?i=22'.format(nove['id']), headers=zaglavlje).status_code == 200
    assert klijent.get('/snimci/{}/presek'.format(sid)).status_code == 401

    # pracenje i izvestaj
    tok = klijent.get('/pacijenti/{}/pracenje'.format(pac), headers=zaglavlje).json()['mozak']
    assert [t['broj_lezija'] for t in tok] == [2, 3] and tok[1]['nove_lezije'] == 1
    iz = klijent.get('/pregledi/{}/izvestaj'.format(p2['id']), headers=zaglavlje).json()
    assert iz['spreman'] and 'novih lezija' in iz['predlog_zakljucka'] and iz['status'] == 'nacrt'
    r = klijent.post('/pregledi/{}/izvestaj/potvrdi'.format(p2['id']), headers=zaglavlje, json={'zakljucak': 'Moj zaključak.'})
    assert r.json()['status'] == 'potvrdjen' and r.json()['zakljucak'] == 'Moj zaključak.'
    assert klijent.put('/pregledi/{}/izvestaj'.format(p2['id']), headers=zaglavlje, json={'zakljucak': 'x'}).status_code == 409
    assert klijent.delete('/pregledi/{}'.format(p2['id']), headers=zaglavlje).status_code == 409
    assert klijent.delete('/pregledi/{}'.format(p1['id']), headers=zaglavlje).status_code == 409   # zavisan kasniji
    assert klijent.post('/pregledi/{}/izvestaj/otvori'.format(p2['id']), headers=zaglavlje).json()['status'] == 'nacrt'
    assert klijent.delete('/pregledi/{}'.format(p2['id']), headers=zaglavlje).status_code == 200
    assert klijent.get('/pregledi/{}'.format(p2['id']), headers=zaglavlje).status_code == 404


def test_kicma_i_greske(klijent, zaglavlje, tmp_path):
    pac = klijent.post('/pacijenti', headers=zaglavlje, json={'ime': 'Mila', 'prezime': 'Milić'}).json()['id']
    fantom(tmp_path / 't2.nii.gz', [(30, 30, 30, 2)], oblik=(48, 80, 40), razmak=(0.5, 0.5, 3.0))
    fantom(tmp_path / 'stir.nii.gz', [(30, 30, 30, 2)], oblik=(48, 80, 40), razmak=(0.5, 0.5, 3.0), seme=3)
    with open(tmp_path / 't2.nii.gz', 'rb') as a, open(tmp_path / 'stir.nii.gz', 'rb') as b:
        r = klijent.post('/pregledi', headers=zaglavlje,
                         files={'t2': ('t2.nii.gz', a), 'dodatna': ('stir.nii.gz', b)},
                         data={'pacijent_id': pac, 'region': 'kicma', 'datum_snimanja': '2025-02-01',
                               'dodatna_sekvenca': 'STIR'})
    assert r.status_code == 200, r.text
    p = _cekaj(klijent, zaglavlje, r.json()['id'])
    rez = p['analize']['sve_lezije']['rezultati']
    assert rez['broj_lezija'] == 1 and rez['tehnika']['ulaz'] == 'T2 + STIR'
    assert 'registracija' in rez['tehnika']
    assert abs(rez['lezije'][0]['zapremina_mm3'] - rez['lezije'][0]['voksela'] * 0.75) < 0.2

    # neispravni unosi
    with open(tmp_path / 't2.nii.gz', 'rb') as f:          # kicma bez druge sekvence nije dozvoljena
        r = klijent.post('/pregledi', headers=zaglavlje, files={'t2': ('t2.nii.gz', f)},
                         data={'pacijent_id': pac, 'region': 'kicma', 'datum_snimanja': '2025-03-01'})
    assert r.status_code == 400
    (tmp_path / 'los.nii.gz').write_bytes(b'nije nifti')
    with open(tmp_path / 'los.nii.gz', 'rb') as f, open(tmp_path / 'stir.nii.gz', 'rb') as b:
        r = klijent.post('/pregledi', headers=zaglavlje, files={'t2': ('los.nii.gz', f), 'dodatna': ('stir.nii.gz', b)},
                         data={'pacijent_id': pac, 'region': 'kicma', 'datum_snimanja': '2025-03-01',
                               'dodatna_sekvenca': 'STIR'})
    assert r.status_code == 400
    with open(tmp_path / 't2.nii.gz', 'rb') as f:
        r = klijent.post('/pregledi', headers=zaglavlje, files={'t2': ('t2.nii.gz', f)},
                         data={'pacijent_id': pac, 'region': 'mozak', 'datum_snimanja': '2025-03-01'})
    assert r.status_code == 400
    assert len(klijent.get('/pacijenti/{}'.format(pac), headers=zaglavlje).json()['pregledi']) == 1
    s = klijent.get('/sistem', headers=zaglavlje).json()
    assert len(s['modeli']) == 3 and not any(m['instaliran'] for m in s['modeli'])
