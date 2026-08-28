from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# --- konekcija (promeni LOZINKU na svoju) ---
KORISNIK = 'postgres'
LOZINKA = 'postgres'
HOST = 'localhost'
PORT = '5432'
BAZA = 'ms_sistem'

URL = f'postgresql+psycopg2://{KORISNIK}:{LOZINKA}@{HOST}:{PORT}/{BAZA}'
engine = create_engine(URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- tabele ---
class Pacijent(Base):
    __tablename__ = 'pacijent'
    id = Column(Integer, primary_key=True)
    ime = Column(String(200), nullable=False)
    datum_rodjenja = Column(String(20))
    napravljen = Column(DateTime, default=datetime.now)
    snimci = relationship('Snimak', back_populates='pacijent')
    pregledi = relationship('Pregled', back_populates='pacijent')

class Snimak(Base):
    __tablename__ = 'snimak'
    id = Column(Integer, primary_key=True)
    pacijent_id = Column(Integer, ForeignKey('pacijent.id'))
    putanja = Column(String(500), nullable=False)
    datum = Column(DateTime, default=datetime.now)
    pacijent = relationship('Pacijent', back_populates='snimci')

class Pregled(Base):
    __tablename__ = 'pregled'
    id = Column(Integer, primary_key=True)
    pacijent_id = Column(Integer, ForeignKey('pacijent.id'))
    snimak_id = Column(Integer, ForeignKey('snimak.id'))
    tip = Column(String(50))            # 'prvi' ili 'kontrola'
    rezultati = Column(Text)            # JSON string sa merenjima
    datum = Column(DateTime, default=datetime.now)
    pacijent = relationship('Pacijent', back_populates='pregledi')

# --- napravi tabele ---
def napravi_tabele():
    Base.metadata.create_all(engine)
    print('Tabele napravljene.')

if __name__ == '__main__':
    napravi_tabele()