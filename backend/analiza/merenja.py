"""Merenje lezija na maski (u standardnoj orijentaciji, isti raspored kao u pregledacu)."""
import numpy as np
from scipy import ndimage

import konfiguracija as kfg

_STRUKTURA = np.ones((3, 3, 3), int)   # 26-susedstvo


def kategorija(p):
    if p >= kfg.PRAG_POUZDANOST_VISOKA:
        return 'visoka'
    if p >= kfg.PRAG_POUZDANOST_SREDNJA:
        return 'srednja'
    return 'niska'


def izmeri(maska_u8, verovatnoca_u8, razmak):
    """Vraca (sazetak, ociscena_maska). Lezije manje od MIN_VOKSELA se uklanjaju kao sum."""
    maska = np.asarray(maska_u8) > 0
    oznake, n = ndimage.label(maska, _STRUKTURA)
    zapremina_voksela = float(razmak[0] * razmak[1] * razmak[2])
    lezije = []
    cista = np.zeros(maska.shape, np.uint8)
    if n:
        indeksi = range(1, n + 1)
        velicine = ndimage.sum(maska, oznake, indeksi)
        centri = ndimage.center_of_mass(maska, oznake, indeksi)
        srednje = ndimage.mean(np.asarray(verovatnoca_u8), oznake, indeksi) / 254.0
        for i, vel, c, p in zip(indeksi, velicine, centri, srednje):
            if vel < kfg.MIN_VOKSELA:
                continue
            cista[oznake == i] = 1
            p = float(min(1.0, p))
            lezije.append({
                'zapremina_mm3': round(float(vel) * zapremina_voksela, 1),
                'voksela': int(vel),
                'centar': [int(round(v)) for v in c],      # (sagitalni, koronalni, aksijalni) indeks
                'pouzdanost': round(p, 3),
                'kategorija': kategorija(p),
            })
    lezije.sort(key=lambda l: -l['zapremina_mm3'])
    for i, l in enumerate(lezije, 1):
        l['broj'] = i
    ukupno = sum(l['zapremina_mm3'] for l in lezije)
    sazetak = {
        'broj_lezija': len(lezije),
        'zapremina_mm3': round(ukupno, 1),
        'zapremina_ml': round(ukupno / 1000.0, 2),
        'najveca_mm3': lezije[0]['zapremina_mm3'] if lezije else 0.0,
        'niska_pouzdanost': sum(1 for l in lezije if l['kategorija'] == 'niska'),
        'lezije': lezije,
    }
    return sazetak, cista
