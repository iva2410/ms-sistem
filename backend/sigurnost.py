"""Lozinke i prijava lekara."""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import konfiguracija as kfg
from baza import Lekar, sesija

_N, _R, _P = 2 ** 14, 8, 1


def hesiraj_lozinku(lozinka: str) -> str:
    so = os.urandom(16)
    h = hashlib.scrypt(lozinka.encode('utf-8'), salt=so, n=_N, r=_R, p=_P, dklen=32)
    return 'scrypt${}${}${}${}${}'.format(
        _N, _R, _P, base64.b64encode(so).decode(), base64.b64encode(h).decode())


def proveri_lozinku(lozinka: str, zapis: str) -> bool:
    try:
        _, n, r, p, so, h = zapis.split('$')
        izracunat = hashlib.scrypt(lozinka.encode('utf-8'), salt=base64.b64decode(so),
                                   n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(izracunat, base64.b64decode(h))
    except Exception:
        return False


def napravi_token(lekar_id: int) -> str:
    istice = datetime.now(timezone.utc) + timedelta(hours=kfg.TRAJANJE_PRIJAVE_H)
    return jwt.encode({'sub': str(lekar_id), 'exp': istice}, kfg.tajni_kljuc(), algorithm='HS256')


_bearer = HTTPBearer(auto_error=False)


def prijavljeni_lekar(podaci: HTTPAuthorizationCredentials = Depends(_bearer),
                      s=Depends(sesija)) -> Lekar:
    greska = HTTPException(status_code=401, detail='Prijava je istekla ili nije važeća. Prijavite se ponovo.')
    if podaci is None:
        raise greska
    try:
        sadrzaj = jwt.decode(podaci.credentials, kfg.tajni_kljuc(), algorithms=['HS256'])
        lekar = s.get(Lekar, int(sadrzaj['sub']))
    except Exception:
        raise greska
    if lekar is None:
        raise greska
    return lekar
