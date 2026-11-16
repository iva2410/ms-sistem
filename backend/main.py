"""MS sistem - API. Pokretanje:  uvicorn main:app --reload  (iz foldera backend)."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import konfiguracija as kfg
import rute_nalog
import rute_pacijenti
import rute_pregledi
from analiza import motor, posao
from baza import napravi_tabele
from sigurnost import prijavljeni_lekar


@asynccontextmanager
async def zivotni_ciklus(app):
    napravi_tabele()
    posao.nastavi_prekinute()
    yield


app = FastAPI(title='MS sistem', lifespan=zivotni_ciklus)
app.add_middleware(CORSMiddleware, allow_origins=kfg.DOZVOLJENI_IZVORI,
                   allow_methods=['*'], allow_headers=['*'])
app.include_router(rute_nalog.ruter)
app.include_router(rute_pacijenti.ruter)
app.include_router(rute_pregledi.ruter)


@app.get('/sistem', dependencies=[Depends(prijavljeni_lekar)])
def sistem():
    """Stanje instalacije: koji modeli postoje i na cemu se izvrsava analiza."""
    return {'modeli': motor.stanje_modela(), 'uredjaj': motor.opis_uredjaja(),
            'registracija_kicma': kfg.KICMA_REGISTRACIJA}
