"""Pregledi: prijem snimaka, analize, preseci za pregledac, izvestaj."""
import shutil
from datetime import date, datetime
from typing import Optional

import nibabel as nib
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

import konfiguracija as kfg
from analiza import nalaz, posao, prikaz
from baza import Analiza, Izvestaj, Lekar, Pacijent, Pregled, Snimak, sesija
from rute_nalog import lekar_json
from rute_pacijenti import pacijent_json, pregled_kratko, stanje_pregleda
from sigurnost import prijavljeni_lekar

ruter = APIRouter(tags=['pregledi'], dependencies=[Depends(prijavljeni_lekar)])
_PNG = {'Cache-Control': 'private, max-age=3600'}


def _pregled(s, pid) -> Pregled:
    p = s.get(Pregled, pid)
    if p is None:
        raise HTTPException(404, 'Pregled nije pronađen.')
    return p


def _prethodni(s, pregled) -> Optional[Pregled]:
    """Poslednji raniji pregled istog regiona za istog pacijenta."""
    return (s.query(Pregled)
            .filter(Pregled.pacijent_id == pregled.pacijent_id, Pregled.region == pregled.region,
                    Pregled.id != pregled.id, Pregled.datum_snimanja < pregled.datum_snimanja)
            .order_by(Pregled.datum_snimanja.desc(), Pregled.id.desc()).first())


def _sacuvaj_snimak(s, pregled, sekvenca, fajl: UploadFile):
    ime = (fajl.filename or '').lower()
    if not (ime.endswith('.nii') or ime.endswith('.nii.gz')):
        raise HTTPException(400, 'Snimak „{}” nije u NIfTI formatu (.nii ili .nii.gz).'.format(fajl.filename))
    folder = kfg.SNIMCI / 'pregled_{}'.format(pregled.id)
    folder.mkdir(parents=True, exist_ok=True)
    putanja = folder / (sekvenca + ('.nii.gz' if ime.endswith('.gz') else '.nii'))
    with open(putanja, 'wb') as f:
        shutil.copyfileobj(fajl.file, f)
    try:
        oblik = nib.load(str(putanja)).shape
        if len([d for d in oblik if d > 1]) != 3:
            raise ValueError('snimak nije trodimenzionalan')
    except Exception as e:
        raise HTTPException(400, 'Snimak „{}” ne može da se učita: {}.'.format(fajl.filename, e))
    s.add(Snimak(pregled_id=pregled.id, sekvenca=sekvenca, putanja=str(putanja),
                 originalno_ime=fajl.filename or ''))


@ruter.post('/pregledi')
def novi_pregled(pacijent_id: int = Form(...), region: str = Form(...),
                 datum_snimanja: date = Form(...), napomena: str = Form(''),
                 dodatna_sekvenca: str = Form(''),
                 flair: Optional[UploadFile] = File(None), t2: Optional[UploadFile] = File(None),
                 dodatna: Optional[UploadFile] = File(None),
                 lekar: Lekar = Depends(prijavljeni_lekar), s=Depends(sesija)):
    if s.get(Pacijent, pacijent_id) is None:
        raise HTTPException(404, 'Pacijent nije pronađen.')
    if region not in ('mozak', 'kicma'):
        raise HTTPException(400, 'Region mora biti mozak ili kičmena moždina.')
    if datum_snimanja > date.today():
        raise HTTPException(400, 'Datum snimanja ne može biti u budućnosti.')
    if region == 'mozak' and flair is None:
        raise HTTPException(400, 'Za pregled mozga učitajte FLAIR snimak.')
    if region == 'kicma' and (t2 is None or dodatna is None):
        raise HTTPException(400, 'Za pregled kičmene moždine učitajte T2 snimak i drugu sekvencu '
                                 '(STIR, PSIR ili MP2RAGE).')
    if region == 'kicma' and dodatna_sekvenca not in posao.DODATNE_SEKVENCE:
        raise HTTPException(400, 'Izaberite vrstu druge sekvence (STIR, PSIR ili MP2RAGE).')

    pregled = Pregled(pacijent_id=pacijent_id, region=region, datum_snimanja=datum_snimanja,
                      napomena=napomena.strip(), lekar_id=lekar.id)
    s.add(pregled)
    s.flush()
    try:
        if region == 'mozak':
            _sacuvaj_snimak(s, pregled, 'FLAIR', flair)
        else:
            _sacuvaj_snimak(s, pregled, 'T2', t2)
            _sacuvaj_snimak(s, pregled, dodatna_sekvenca, dodatna)
    except HTTPException:
        s.rollback()
        shutil.rmtree(kfg.SNIMCI / 'pregled_{}'.format(pregled.id), ignore_errors=True)
        raise

    analize = [Analiza(pregled_id=pregled.id, tip='sve_lezije', korak='Čeka na red')]
    prethodni = _prethodni(s, pregled)
    if region == 'mozak' and prethodni is not None:
        analize.append(Analiza(pregled_id=pregled.id, tip='nove_lezije', korak='Čeka na red',
                               prethodni_pregled_id=prethodni.id))
    s.add_all(analize)
    s.commit()
    for a in analize:
        posao.dodaj(a.id)
    return {'id': pregled.id}


def _analiza_json(a: Analiza):
    return {'id': a.id, 'tip': a.tip, 'status': a.status, 'korak': a.korak, 'napredak': a.napredak,
            'greska': a.greska, 'trajanje_s': a.trajanje_s,
            'rezultati': nalaz.rezultati(a)}


@ruter.get('/pregledi/{pid}')
def pregled(pid: int, s=Depends(sesija)):
    p = _pregled(s, pid)
    prethodni = _prethodni(s, p)
    snimci = []
    for sn in p.snimci:
        try:
            meta = prikaz.pripremi_snimak(sn.putanja, posao.kes_snimka(sn.id))
        except Exception as e:
            meta = {'oblik': None, 'razmak': None, 'greska': str(e)}
        snimci.append({'id': sn.id, 'sekvenca': sn.sekvenca, 'ime': sn.originalno_ime, **meta})
    return {
        'id': p.id, 'region': p.region, 'datum_snimanja': p.datum_snimanja.isoformat(),
        'napomena': p.napomena, 'stanje': stanje_pregleda(p),
        'lekar': p.lekar.puno_ime if p.lekar else '',
        'pacijent': pacijent_json(p.pacijent),
        'snimci': snimci,
        'analize': {a.tip: _analiza_json(a) for a in sorted(p.analize, key=lambda x: x.id)},
        'prethodni': pregled_kratko(prethodni) if prethodni else None,
        'izvestaj_status': p.izvestaj.status if p.izvestaj else 'nacrt',
    }


@ruter.post('/analize/{aid}/ponovi')
def ponovi(aid: int, s=Depends(sesija)):
    a = s.get(Analiza, aid)
    if a is None:
        raise HTTPException(404, 'Analiza nije pronađena.')
    if a.status in ('na_cekanju', 'u_toku'):
        raise HTTPException(409, 'Analiza je već u toku.')
    a.status, a.korak, a.napredak, a.greska = 'na_cekanju', 'Čeka na red', 0, ''
    s.commit()
    posao.dodaj(a.id)
    return {'id': a.id}


@ruter.delete('/pregledi/{pid}')
def obrisi(pid: int, s=Depends(sesija)):
    p = _pregled(s, pid)
    if any(a.status == 'u_toku' for a in p.analize):
        raise HTTPException(409, 'Analiza je u toku; pregled se može obrisati kada se završi.')
    if p.izvestaj is not None and p.izvestaj.status == 'potvrdjen':
        raise HTTPException(409, 'Pregled sa potvrđenim izveštajem ne može se obrisati.')
    zavisne = s.query(Analiza).filter(Analiza.prethodni_pregled_id == p.id).count()
    if zavisne:
        raise HTTPException(409, 'Kasniji pregled je upoređen sa ovim; prvo obrišite kasniji pregled.')
    folderi = [kfg.SNIMCI / 'pregled_{}'.format(p.id)] + [kfg.ANALIZE / 'analiza_{}'.format(a.id) for a in p.analize]
    kesevi = [posao.kes_snimka(sn.id) for sn in p.snimci]
    s.delete(p)
    s.commit()
    for f in folderi:
        shutil.rmtree(f, ignore_errors=True)
    for k in kesevi:
        k.unlink(missing_ok=True)
        k.with_suffix('.json').unlink(missing_ok=True)
    return {'obrisan': pid}


# ---------- preseci za pregledac ----------
def _ravan(ravan):
    if ravan not in prikaz.RAVNI:
        raise HTTPException(400, 'Nepoznata ravan.')


@ruter.get('/snimci/{sid}/presek')
def presek_snimka(sid: int, ravan: str = 'aksijalni', i: int = 0, s=Depends(sesija)):
    _ravan(ravan)
    sn = s.get(Snimak, sid)
    if sn is None:
        raise HTTPException(404, 'Snimak nije pronađen.')
    kes = posao.kes_snimka(sn.id)
    meta = prikaz.pripremi_snimak(sn.putanja, kes)
    return Response(prikaz.png_snimka(kes, meta, ravan, i), media_type='image/png', headers=_PNG)


def _zavrsena(s, aid) -> Analiza:
    a = s.get(Analiza, aid)
    if a is None or a.status != 'zavrsena':
        raise HTTPException(404, 'Rezultat analize nije dostupan.')
    return a


@ruter.get('/analize/{aid}/sloj')
def sloj(aid: int, vrsta: str = 'lezije', ravan: str = 'aksijalni', i: int = 0, s=Depends(sesija)):
    _ravan(ravan)
    a = _zavrsena(s, aid)
    r = nalaz.rezultati(a)
    meta = {'razmak': r['razmak']}
    if vrsta == 'pouzdanost':
        fajl, boja = 'verovatnoca.npy', 'pouzdanost'
    elif vrsta == 'lezije':
        fajl, boja = 'maska.npy', ('nove' if a.tip == 'nove_lezije' else 'lezije')
    else:
        raise HTTPException(400, 'Nepoznat sloj.')
    return Response(prikaz.png_sloja(kfg.ANALIZE / 'analiza_{}'.format(a.id) / fajl, meta, ravan, i, boja),
                    media_type='image/png', headers=_PNG)


@ruter.get('/analize/{aid}/raniji')
def raniji_presek(aid: int, ravan: str = 'aksijalni', i: int = 0, s=Depends(sesija)):
    """Raniji snimak poravnat na noviji (za uporedni prikaz)."""
    _ravan(ravan)
    a = _zavrsena(s, aid)
    kes = kfg.ANALIZE / 'analiza_{}'.format(a.id) / 'raniji.npy'
    if not kes.exists():
        raise HTTPException(404, 'Poravnat raniji snimak nije dostupan.')
    meta = {'razmak': nalaz.rezultati(a)['razmak']}
    return Response(prikaz.png_snimka(kes, meta, ravan, i), media_type='image/png', headers=_PNG)


# ---------- izvestaj ----------
class IzvestajIzmena(BaseModel):
    zakljucak: str


def _izvestaj_json(s, p: Pregled):
    sve = nalaz.rezultati(nalaz.analiza_tipa(p, 'sve_lezije'))
    nove = nalaz.rezultati(nalaz.analiza_tipa(p, 'nove_lezije'))
    prethodni = _prethodni(s, p)
    prethodni_sve = nalaz.rezultati(nalaz.analiza_tipa(prethodni, 'sve_lezije')) if prethodni else None
    iz = p.izvestaj
    lekar = (iz.lekar if iz and iz.lekar else p.lekar)
    predlog = nalaz.predlog_zakljucka(p, sve, nove, prethodni, prethodni_sve)
    return {
        'pregled_id': p.id, 'region': p.region, 'datum_snimanja': p.datum_snimanja.isoformat(),
        'sekvence': [sn.sekvenca for sn in p.snimci],
        'pacijent': pacijent_json(p.pacijent),
        'lekar': lekar_json(lekar) if lekar else None,
        'spreman': sve is not None and stanje_pregleda(p) not in ('u_toku', 'greska'),
        'sve': sve, 'nove': nove,
        'prethodni': ({'datum_snimanja': prethodni.datum_snimanja.isoformat(),
                       'broj_lezija': prethodni_sve['broj_lezija'] if prethodni_sve else None,
                       'zapremina_ml': prethodni_sve['zapremina_ml'] if prethodni_sve else None}
                      if prethodni else None),
        'tehnika': nalaz.tehnika_redovi(sve, nove),
        'predlog_zakljucka': predlog,
        'zakljucak': iz.zakljucak if iz and iz.zakljucak else predlog,
        'status': iz.status if iz else 'nacrt',
        'potvrdjen': iz.potvrdjen.isoformat(timespec='minutes') if iz and iz.potvrdjen else None,
        'napomena': nalaz.NAPOMENA,
    }


@ruter.get('/pregledi/{pid}/izvestaj')
def izvestaj(pid: int, s=Depends(sesija)):
    return _izvestaj_json(s, _pregled(s, pid))


def _izvestaj_zapis(s, p, lekar) -> Izvestaj:
    if p.izvestaj is None:
        p.izvestaj = Izvestaj(pregled_id=p.id, lekar_id=lekar.id)
        s.flush()
    return p.izvestaj


@ruter.put('/pregledi/{pid}/izvestaj')
def sacuvaj_izvestaj(pid: int, izmena: IzvestajIzmena, lekar: Lekar = Depends(prijavljeni_lekar),
                     s=Depends(sesija)):
    p = _pregled(s, pid)
    iz = _izvestaj_zapis(s, p, lekar)
    if iz.status == 'potvrdjen':
        raise HTTPException(409, 'Izveštaj je potvrđen. Otvorite ga za izmenu da biste menjali zaključak.')
    iz.zakljucak, iz.lekar_id, iz.izmenjen = izmena.zakljucak.strip(), lekar.id, datetime.now()
    s.commit()
    return _izvestaj_json(s, p)


@ruter.post('/pregledi/{pid}/izvestaj/potvrdi')
def potvrdi_izvestaj(pid: int, izmena: IzvestajIzmena, lekar: Lekar = Depends(prijavljeni_lekar),
                     s=Depends(sesija)):
    p = _pregled(s, pid)
    if stanje_pregleda(p) in ('u_toku', 'greska', 'bez_analize'):
        raise HTTPException(409, 'Izveštaj se može potvrditi kada se analiza uspešno završi.')
    if not izmena.zakljucak.strip():
        raise HTTPException(400, 'Zaključak ne može biti prazan.')
    iz = _izvestaj_zapis(s, p, lekar)
    iz.zakljucak, iz.lekar_id = izmena.zakljucak.strip(), lekar.id
    iz.status, iz.potvrdjen, iz.izmenjen = 'potvrdjen', datetime.now(), datetime.now()
    s.commit()
    return _izvestaj_json(s, p)


@ruter.post('/pregledi/{pid}/izvestaj/otvori')
def otvori_izvestaj(pid: int, lekar: Lekar = Depends(prijavljeni_lekar), s=Depends(sesija)):
    p = _pregled(s, pid)
    iz = _izvestaj_zapis(s, p, lekar)
    iz.status, iz.potvrdjen, iz.izmenjen = 'nacrt', None, datetime.now()
    s.commit()
    return _izvestaj_json(s, p)
