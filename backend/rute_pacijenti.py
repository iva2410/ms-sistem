"""Pacijenti: radna lista, karton, pracenje kroz vreme."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_

from analiza import nalaz
from baza import Lekar, Pacijent, sesija
from sigurnost import prijavljeni_lekar

ruter = APIRouter(prefix='/pacijenti', tags=['pacijenti'], dependencies=[Depends(prijavljeni_lekar)])


class PacijentPodaci(BaseModel):
    ime: str = Field(min_length=1, max_length=100)
    prezime: str = Field(min_length=1, max_length=100)
    broj_kartona: str = Field(default='', max_length=40)
    datum_rodjenja: Optional[date] = None
    pol: str = Field(default='', pattern='^(M|Z|)$')
    napomena: str = ''


def stanje_pregleda(p):
    """Zbirno stanje pregleda za prikaz u listama."""
    statusi = [a.status for a in p.analize]
    if not statusi:
        return 'bez_analize'
    if 'greska' in statusi:
        return 'greska'
    if any(st in ('na_cekanju', 'u_toku') for st in statusi):
        return 'u_toku'
    if p.izvestaj is not None and p.izvestaj.status == 'potvrdjen':
        return 'potvrdjen'
    return 'za_pregled'


def pacijent_json(p: Pacijent, sa_pregledima=False):
    pregledi = sorted(p.pregledi, key=lambda x: (x.datum_snimanja, x.id), reverse=True)
    poslednji = pregledi[0] if pregledi else None
    d = {'id': p.id, 'ime': p.ime, 'prezime': p.prezime, 'broj_kartona': p.broj_kartona,
         'datum_rodjenja': p.datum_rodjenja.isoformat() if p.datum_rodjenja else None,
         'pol': p.pol, 'napomena': p.napomena, 'broj_pregleda': len(pregledi),
         'poslednji_pregled': None}
    if poslednji:
        d['poslednji_pregled'] = {'id': poslednji.id, 'datum_snimanja': poslednji.datum_snimanja.isoformat(),
                                  'region': poslednji.region, 'stanje': stanje_pregleda(poslednji)}
    if sa_pregledima:
        d['pregledi'] = [pregled_kratko(x) for x in pregledi]
    return d


def pregled_kratko(p):
    sve = nalaz.rezultati(nalaz.analiza_tipa(p, 'sve_lezije'))
    nove = nalaz.rezultati(nalaz.analiza_tipa(p, 'nove_lezije'))
    return {'id': p.id, 'region': p.region, 'datum_snimanja': p.datum_snimanja.isoformat(),
            'sekvence': [sn.sekvenca for sn in p.snimci], 'stanje': stanje_pregleda(p),
            'broj_lezija': sve['broj_lezija'] if sve else None,
            'zapremina_ml': sve['zapremina_ml'] if sve else None,
            'nove_lezije': nove['broj_lezija'] if nove else None,
            'lekar': p.lekar.puno_ime if p.lekar else ''}


@ruter.get('')
def lista(pretraga: str = '', s=Depends(sesija)):
    q = s.query(Pacijent)
    if pretraga.strip():
        for rec in pretraga.strip().split():
            uzorak = '%{}%'.format(rec)
            q = q.filter(or_(Pacijent.ime.ilike(uzorak), Pacijent.prezime.ilike(uzorak),
                             Pacijent.broj_kartona.ilike(uzorak)))
    return [pacijent_json(p) for p in q.order_by(Pacijent.prezime, Pacijent.ime).all()]


@ruter.post('')
def dodaj(p: PacijentPodaci, lekar: Lekar = Depends(prijavljeni_lekar), s=Depends(sesija)):
    novi = Pacijent(napravio_id=lekar.id, **_ocisti(p))
    s.add(novi)
    s.commit()
    return pacijent_json(novi)


def _ocisti(p: PacijentPodaci):
    d = p.model_dump()
    for k in ('ime', 'prezime', 'broj_kartona', 'napomena'):
        d[k] = d[k].strip()
    return d


def _nadji(s, pid) -> Pacijent:
    p = s.get(Pacijent, pid)
    if p is None:
        raise HTTPException(404, 'Pacijent nije pronađen.')
    return p


@ruter.get('/{pid}')
def karton(pid: int, s=Depends(sesija)):
    return pacijent_json(_nadji(s, pid), sa_pregledima=True)


@ruter.put('/{pid}')
def izmeni(pid: int, podaci: PacijentPodaci, s=Depends(sesija)):
    p = _nadji(s, pid)
    for k, v in _ocisti(podaci).items():
        setattr(p, k, v)
    s.commit()
    return pacijent_json(p)


@ruter.get('/{pid}/pracenje')
def pracenje(pid: int, s=Depends(sesija)):
    """Broj i zapremina lezija kroz vreme, odvojeno za mozak i kicmenu mozdinu."""
    p = _nadji(s, pid)
    izlaz = {'mozak': [], 'kicma': []}
    for pr in sorted(p.pregledi, key=lambda x: (x.datum_snimanja, x.id)):
        sve = nalaz.rezultati(nalaz.analiza_tipa(pr, 'sve_lezije'))
        if not sve:
            continue
        nove = nalaz.rezultati(nalaz.analiza_tipa(pr, 'nove_lezije'))
        izlaz[pr.region].append({
            'pregled_id': pr.id, 'datum': pr.datum_snimanja.isoformat(),
            'broj_lezija': sve['broj_lezija'], 'zapremina_ml': sve['zapremina_ml'],
            'nove_lezije': nove['broj_lezija'] if nove else None})
    return izlaz
