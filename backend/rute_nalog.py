"""Registracija i prijava lekara."""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from baza import Lekar, sesija
from sigurnost import hesiraj_lozinku, napravi_token, prijavljeni_lekar, proveri_lozinku

ruter = APIRouter(prefix='/nalog', tags=['nalog'])
_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class Profil(BaseModel):
    ime: str = Field(min_length=1, max_length=100)
    prezime: str = Field(min_length=1, max_length=100)
    titula: str = Field(default='', max_length=60)
    specijalnost: str = Field(default='', max_length=120)
    ustanova: str = Field(default='', max_length=200)
    broj_licence: str = Field(default='', max_length=60)


class Registracija(Profil):
    email: str = Field(max_length=200)
    lozinka: str = Field(min_length=8, max_length=200)


class Prijava(BaseModel):
    email: str
    lozinka: str


def lekar_json(l: Lekar):
    return {'id': l.id, 'email': l.email, 'ime': l.ime, 'prezime': l.prezime, 'titula': l.titula,
            'specijalnost': l.specijalnost, 'ustanova': l.ustanova, 'broj_licence': l.broj_licence,
            'puno_ime': l.puno_ime}


@ruter.post('/registracija')
def registracija(p: Registracija, s=Depends(sesija)):
    email = p.email.strip().lower()
    if not _EMAIL.match(email):
        raise HTTPException(400, 'Adresa e-pošte nije ispravna.')
    if s.query(Lekar).filter_by(email=email).first():
        raise HTTPException(409, 'Nalog sa ovom adresom e-pošte već postoji.')
    l = Lekar(email=email, lozinka_hash=hesiraj_lozinku(p.lozinka), ime=p.ime.strip(),
              prezime=p.prezime.strip(), titula=p.titula.strip(), specijalnost=p.specijalnost.strip(),
              ustanova=p.ustanova.strip(), broj_licence=p.broj_licence.strip())
    s.add(l)
    s.commit()
    return {'token': napravi_token(l.id), 'lekar': lekar_json(l)}


@ruter.post('/prijava')
def prijava(p: Prijava, s=Depends(sesija)):
    l = s.query(Lekar).filter_by(email=p.email.strip().lower()).first()
    if l is None or not proveri_lozinku(p.lozinka, l.lozinka_hash):
        raise HTTPException(401, 'Adresa e-pošte ili lozinka nisu ispravni.')
    return {'token': napravi_token(l.id), 'lekar': lekar_json(l)}


@ruter.get('/ja')
def ja(lekar: Lekar = Depends(prijavljeni_lekar)):
    return lekar_json(lekar)


@ruter.put('/ja')
def izmeni_profil(p: Profil, lekar: Lekar = Depends(prijavljeni_lekar), s=Depends(sesija)):
    l = s.get(Lekar, lekar.id)
    for polje, vrednost in p.model_dump().items():
        setattr(l, polje, vrednost.strip())
    s.commit()
    return lekar_json(l)
