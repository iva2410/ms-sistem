"""Tabele baze podataka."""
from datetime import datetime

from sqlalchemy import (Column, Date, DateTime, Float, ForeignKey, Integer, String, Text,
                        create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import konfiguracija as kfg

_argumenti = {'check_same_thread': False} if kfg.BAZA_URL.startswith('sqlite') else {}
engine = create_engine(kfg.BAZA_URL, connect_args=_argumenti, pool_pre_ping=True)
Sesija = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class Lekar(Base):
    __tablename__ = 'ms_lekar'
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    lozinka_hash = Column(String(300), nullable=False)
    ime = Column(String(100), nullable=False)
    prezime = Column(String(100), nullable=False)
    titula = Column(String(60), default='')
    specijalnost = Column(String(120), default='')
    ustanova = Column(String(200), default='')
    broj_licence = Column(String(60), default='')
    napravljen = Column(DateTime, default=datetime.now)

    @property
    def puno_ime(self):
        return ' '.join(x for x in (self.titula, self.ime, self.prezime) if x)


class Pacijent(Base):
    __tablename__ = 'ms_pacijent'
    id = Column(Integer, primary_key=True)
    broj_kartona = Column(String(40), index=True, default='')
    ime = Column(String(100), nullable=False)
    prezime = Column(String(100), nullable=False)
    datum_rodjenja = Column(Date)
    pol = Column(String(1), default='')          # 'M', 'Z' ili ''
    napomena = Column(Text, default='')
    napravio_id = Column(Integer, ForeignKey('ms_lekar.id'))
    napravljen = Column(DateTime, default=datetime.now)
    pregledi = relationship('Pregled', back_populates='pacijent', cascade='all, delete-orphan')


class Pregled(Base):
    __tablename__ = 'ms_pregled'
    id = Column(Integer, primary_key=True)
    pacijent_id = Column(Integer, ForeignKey('ms_pacijent.id'), nullable=False, index=True)
    region = Column(String(10), nullable=False)   # 'mozak' ili 'kicma'
    datum_snimanja = Column(Date, nullable=False)
    napomena = Column(Text, default='')
    lekar_id = Column(Integer, ForeignKey('ms_lekar.id'))
    napravljen = Column(DateTime, default=datetime.now)
    pacijent = relationship('Pacijent', back_populates='pregledi')
    lekar = relationship('Lekar')
    snimci = relationship('Snimak', back_populates='pregled', cascade='all, delete-orphan')
    analize = relationship('Analiza', back_populates='pregled', cascade='all, delete-orphan',
                           foreign_keys='Analiza.pregled_id')
    izvestaj = relationship('Izvestaj', back_populates='pregled', uselist=False,
                            cascade='all, delete-orphan')


class Snimak(Base):
    __tablename__ = 'ms_snimak'
    id = Column(Integer, primary_key=True)
    pregled_id = Column(Integer, ForeignKey('ms_pregled.id'), nullable=False, index=True)
    sekvenca = Column(String(20), nullable=False)  # FLAIR, T2, STIR, PSIR, MP2RAGE
    putanja = Column(String(500), nullable=False)
    originalno_ime = Column(String(300), default='')
    pregled = relationship('Pregled', back_populates='snimci')


class Analiza(Base):
    __tablename__ = 'ms_analiza'
    id = Column(Integer, primary_key=True)
    pregled_id = Column(Integer, ForeignKey('ms_pregled.id'), nullable=False, index=True)
    tip = Column(String(20), nullable=False)       # 'sve_lezije' ili 'nove_lezije'
    status = Column(String(20), default='na_cekanju')  # na_cekanju, u_toku, zavrsena, greska
    korak = Column(String(200), default='')
    napredak = Column(Integer, default=0)
    greska = Column(Text, default='')
    model = Column(String(120), default='')
    prethodni_pregled_id = Column(Integer, ForeignKey('ms_pregled.id'))
    rezultati = Column(Text, default='')           # JSON
    folder = Column(String(500), default='')
    napravljena = Column(DateTime, default=datetime.now)
    zavrsena = Column(DateTime)
    trajanje_s = Column(Float)
    pregled = relationship('Pregled', back_populates='analize', foreign_keys=[pregled_id])


class Izvestaj(Base):
    __tablename__ = 'ms_izvestaj'
    id = Column(Integer, primary_key=True)
    pregled_id = Column(Integer, ForeignKey('ms_pregled.id'), unique=True, nullable=False)
    zakljucak = Column(Text, default='')
    status = Column(String(20), default='nacrt')   # 'nacrt' ili 'potvrdjen'
    lekar_id = Column(Integer, ForeignKey('ms_lekar.id'))
    izmenjen = Column(DateTime, default=datetime.now)
    potvrdjen = Column(DateTime)
    pregled = relationship('Pregled', back_populates='izvestaj')
    lekar = relationship('Lekar')


def napravi_tabele():
    Base.metadata.create_all(engine)


def sesija():
    """FastAPI zavisnost: jedna sesija po zahtevu."""
    s = Sesija()
    try:
        yield s
    finally:
        s.close()


if __name__ == '__main__':
    napravi_tabele()
    print('Tabele su napravljene.')
