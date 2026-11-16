"""Priprema snimaka i slojeva za prikaz u pregledacu.

Svaki volumen se jednom prevodi u standardnu orijentaciju (RAS) i cuva kao uint8 .npy,
pa se preseci citaju brzo (memmap).
"""
import io
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image

RAVNI = ('aksijalni', 'koronalni', 'sagitalni')
_OSA = {'sagitalni': 0, 'koronalni': 1, 'aksijalni': 2}
MAKS_STRANA = 768


def _kanonski(putanja):
    img = nib.as_closest_canonical(nib.load(str(putanja)))
    podaci = np.asanyarray(img.dataobj)
    if podaci.ndim == 4 and podaci.shape[3] == 1:
        podaci = podaci[..., 0]
    if podaci.ndim != 3:
        raise ValueError('Snimak mora biti trodimenzionalan (dobijeno {} dimenzija).'.format(podaci.ndim))
    razmak = [float(v) for v in img.header.get_zooms()[:3]]
    return podaci, razmak


def pripremi_snimak(nifti_putanja, kes_putanja):
    """Sivi snimak -> uint8 (prozor 0.5-99.5 percentil). Vraca meta podatke."""
    kes_putanja = Path(kes_putanja)
    meta_p = kes_putanja.with_suffix('.json')
    if kes_putanja.exists() and meta_p.exists():
        return json.loads(meta_p.read_text())
    podaci, razmak = _kanonski(nifti_putanja)
    podaci = np.nan_to_num(podaci.astype(np.float32))
    pozitivni = podaci[podaci > 0]
    if pozitivni.size:
        lo, hi = np.percentile(pozitivni, [0.5, 99.5])
    else:
        lo, hi = 0.0, 1.0
    if hi <= lo:
        hi = lo + 1.0
    u8 = (np.clip((podaci - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    kes_putanja.parent.mkdir(parents=True, exist_ok=True)
    np.save(kes_putanja, u8)
    meta = {'oblik': [int(v) for v in u8.shape], 'razmak': razmak}
    meta_p.write_text(json.dumps(meta))
    return meta


def pripremi_sloj(nifti_putanja, kes_putanja):
    """Maska ili mapa verovatnoce (vec 0-255) -> uint8 u standardnoj orijentaciji."""
    kes_putanja = Path(kes_putanja)
    if kes_putanja.exists():
        return
    podaci, _ = _kanonski(nifti_putanja)
    kes_putanja.parent.mkdir(parents=True, exist_ok=True)
    np.save(kes_putanja, np.asarray(podaci).astype(np.uint8))


def _presek(vol, ravan, indeks):
    osa = _OSA[ravan]
    indeks = int(np.clip(indeks, 0, vol.shape[osa] - 1))
    if ravan == 'aksijalni':
        a = vol[:, :, indeks]
    elif ravan == 'koronalni':
        a = vol[:, indeks, :]
    else:
        a = vol[indeks, :, :]
    # radioloska konvencija: desna strana pacijenta levo na ekranu, napred/gore na vrhu
    return np.ascontiguousarray(a.T[::-1, ::-1])


def _velicina(oblik_preseka, ravan, razmak):
    sx, sy, sz = razmak
    red, kol = {'aksijalni': (sy, sx), 'koronalni': (sz, sx), 'sagitalni': (sz, sy)}[ravan]
    najmanji = min(red, kol)
    v = oblik_preseka[0] * red / najmanji
    s = oblik_preseka[1] * kol / najmanji
    faktor = min(1.0, MAKS_STRANA / max(v, s))
    return max(1, int(round(s * faktor))), max(1, int(round(v * faktor)))


def _png(slika):
    buf = io.BytesIO()
    slika.save(buf, format='PNG', compress_level=1)
    return buf.getvalue()


def png_snimka(kes_putanja, meta, ravan, indeks):
    vol = np.load(kes_putanja, mmap_mode='r')
    a = _presek(vol, ravan, indeks)
    slika = Image.fromarray(a, mode='L').resize(_velicina(a.shape, ravan, meta['razmak']), Image.BILINEAR)
    return _png(slika)


_BOJE = {'lezije': (255, 176, 0), 'nove': (255, 61, 139)}


def png_sloja(kes_putanja, meta, ravan, indeks, vrsta):
    """Providan PNG sloj. vrsta: 'lezije', 'nove' (maske) ili 'pouzdanost' (mapa 0-254)."""
    vol = np.load(kes_putanja, mmap_mode='r')
    a = _presek(vol, ravan, indeks)
    vel = _velicina(a.shape, ravan, meta['razmak'])
    rgba = np.zeros(a.shape + (4,), np.uint8)
    if vrsta == 'pouzdanost':
        p = a.astype(np.float32) / 254.0
        vidljivo = p >= 0.10
        # od plave (nisko) preko zute do crvene (visoko)
        rgba[..., 0] = np.clip(255 * np.minimum(1, p * 2), 0, 255)
        rgba[..., 1] = np.clip(255 * (1 - np.abs(p - 0.5) * 2), 0, 255)
        rgba[..., 2] = np.clip(255 * np.maximum(0, 1 - p * 2), 0, 255)
        rgba[..., 3] = np.where(vidljivo, 200, 0)
        slika = Image.fromarray(rgba, mode='RGBA').resize(vel, Image.BILINEAR)
    else:
        r, g, b = _BOJE.get(vrsta, _BOJE['lezije'])
        m = a > 0
        rgba[m] = (r, g, b, 255)
        slika = Image.fromarray(rgba, mode='RGBA').resize(vel, Image.NEAREST)
    return _png(slika)
