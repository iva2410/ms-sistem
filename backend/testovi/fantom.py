"""Vestacki snimci i zamena za model - SAMO za automatske testove."""
import nibabel as nib
import numpy as np


def fantom(putanja, lezije, oblik=(64, 72, 56), razmak=(1.0, 1.0, 1.2), pomeraj=(0, 0, 0), seme=0):
    """Elipsoid ('glava') sa svetlim kuglicama ('lezije'). lezije: lista (x, y, z, poluprecnik)."""
    rng = np.random.default_rng(seme)
    x, y, z = np.meshgrid(*[np.arange(n) for n in oblik], indexing='ij')
    c = [n / 2 + p for n, p in zip(oblik, pomeraj)]
    glava = (((x - c[0]) / (oblik[0] * 0.40)) ** 2 + ((y - c[1]) / (oblik[1] * 0.42)) ** 2 +
             ((z - c[2]) / (oblik[2] * 0.40)) ** 2) < 1
    vol = np.where(glava, 300.0, 0.0) + rng.normal(0, 8, oblik) * glava
    vol += 60 * np.sin(x / 5.0) * glava                      # struktura, da registracija ima oslonac
    for lx, ly, lz, r in lezije:
        k = ((x - lx - pomeraj[0]) ** 2 + (y - ly - pomeraj[1]) ** 2 + (z - lz - pomeraj[2]) ** 2) < r * r
        vol[k] = 900.0
    nib.save(nib.Nifti1Image(vol.astype(np.float32), np.diag(list(razmak) + [1.0])), str(putanja))


def lazni_model(kljuc, kanali, izlaz_dir):
    """Zamena za motor.segmentuj: prag po intenzitetu. Kod 2 kanala 'novo' = svetlo samo na drugom."""
    from pathlib import Path
    izlaz_dir = Path(izlaz_dir)
    slike = [nib.load(str(k)) for k in kanali]
    podaci = [np.asanyarray(s.dataobj).astype(np.float32) for s in slike]
    if kljuc == 'mozak_nove':
        maska = (podaci[1] > 700) & (podaci[0] < 700)
    else:
        maska = podaci[0] > 700
    verov = np.where(maska, 240, 5).astype(np.uint8)
    ref = slike[-1] if kljuc == 'mozak_nove' else slike[0]
    nib.save(nib.Nifti1Image(maska.astype(np.uint8), ref.affine), str(izlaz_dir / 'maska.nii.gz'))
    nib.save(nib.Nifti1Image(verov, ref.affine), str(izlaz_dir / 'verovatnoca.nii.gz'))
    return izlaz_dir / 'maska.nii.gz', izlaz_dir / 'verovatnoca.nii.gz', {
        'model': 'test', 'folder': 'test', 'checkpoint': 'test', 'uredjaj': 'CPU'}
