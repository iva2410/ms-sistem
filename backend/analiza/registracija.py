"""Poravnanje snimaka (SimpleITK)."""
import math

import SimpleITK as sitk


def _mi(fiksni, pokretni_na_mrezi):
    r = sitk.ImageRegistrationMethod()
    r.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    r.SetMetricSamplingStrategy(r.RANDOM)
    r.SetMetricSamplingPercentage(0.1, seed=42)
    r.SetInterpolator(sitk.sitkLinear)
    r.SetInitialTransform(sitk.Transform(3, sitk.sitkIdentity))
    return float(r.MetricEvaluate(fiksni, pokretni_na_mrezi))


def _na_mrezu(pokretni, fiksni, tx):
    return sitk.Resample(pokretni, fiksni, tx, sitk.sitkLinear, 0.0, sitk.sitkFloat32)


def _rigidna(fiksni, pokretni, pocetna):
    r = sitk.ImageRegistrationMethod()
    r.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    r.SetMetricSamplingStrategy(r.RANDOM)
    r.SetMetricSamplingPercentage(0.1, seed=42)
    r.SetInterpolator(sitk.sitkLinear)
    r.SetOptimizerAsRegularStepGradientDescent(1.0, 1e-4, 150, relaxationFactor=0.5)
    r.SetOptimizerScalesFromPhysicalShift()
    r.SetShrinkFactorsPerLevel([4, 2, 1])
    r.SetSmoothingSigmasPerLevel([2, 1, 0])
    r.SetInitialTransform(pocetna, inPlace=False)
    return r.Execute(fiksni, pokretni)


def _opis(tx):
    """Pomeraj (mm) i rotacija (stepeni) rigidne transformacije."""
    try:
        e = sitk.Euler3DTransform(tx) if not isinstance(tx, sitk.CompositeTransform) \
            else sitk.Euler3DTransform(tx.GetBackTransform())
        t = e.GetTranslation()
        ugao = max(abs(e.GetAngleX()), abs(e.GetAngleY()), abs(e.GetAngleZ()))
        return round(math.sqrt(sum(v * v for v in t)), 1), round(math.degrees(ugao), 1)
    except Exception:
        return None, None


def poravnaj_vremenske_tacke(fiksni_putanja, pokretni_putanja, izlaz_putanja):
    """Raniji snimak (pokretni) poravnava na noviji (fiksni) i upisuje ga na mrezu novijeg.

    Dva snimanja istog pacijenta: rigidna registracija, pocetak iz poravnanja tezista.
    """
    fiksni = sitk.ReadImage(str(fiksni_putanja), sitk.sitkFloat32)
    pokretni = sitk.ReadImage(str(pokretni_putanja), sitk.sitkFloat32)
    pocetna = sitk.CenteredTransformInitializer(
        fiksni, pokretni, sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS)
    samo_centrirano = _na_mrezu(pokretni, fiksni, pocetna)
    mi_pre = _mi(fiksni, samo_centrirano)
    info = {'metoda': 'rigidna (6 parametara, Mattes MI)', 'mi_pre': round(mi_pre, 4)}
    try:
        tx = _rigidna(fiksni, pokretni, pocetna)
        poravnat = _na_mrezu(pokretni, fiksni, tx)
        mi_posle = _mi(fiksni, poravnat)
        # prihvata se osim ako je jasno losija od pocetnog poravnanja (1% tolerancije na sum uzorkovanja)
        if mi_posle <= mi_pre + 0.01 * abs(mi_pre):
            pomeraj, rotacija = _opis(tx)
            info.update(mi_posle=round(mi_posle, 4), primenjena=True,
                        pomeraj_mm=pomeraj, rotacija_step=rotacija)
        else:                                   # registracija pogorsala poravnanje
            poravnat = samo_centrirano
            info.update(mi_posle=round(mi_posle, 4), primenjena=False,
                        upozorenje='Registracija nije poboljšala poravnanje; zadržano početno poravnanje.')
    except Exception as e:
        poravnat = samo_centrirano
        info.update(primenjena=False, upozorenje='Registracija nije uspela ({}).'.format(e))
    sitk.WriteImage(poravnat, str(izlaz_putanja))
    return info


def dodatna_na_t2(t2_putanja, dodatna_putanja, izlaz_putanja, rezim='zasticena'):
    """Dodatnu sekvencu (isto snimanje) prebacuje na mrezu T2 snimka.

    rezim 'bez': samo preuzorkovanje po koordinatama skenera.
    rezim 'zasticena': rigidna registracija od identiteta, zadrzava se samo ako popravlja poravnanje.
    """
    fiksni = sitk.ReadImage(str(t2_putanja), sitk.sitkFloat32)
    pokretni = sitk.ReadImage(str(dodatna_putanja), sitk.sitkFloat32)
    bez = _na_mrezu(pokretni, fiksni, sitk.Transform(3, sitk.sitkIdentity))
    info = {'metoda': 'preuzorkovanje na T2 mrežu', 'primenjena': False}
    rezultat = bez
    if rezim == 'zasticena':
        try:
            mi_pre = _mi(fiksni, bez)
            pocetna = sitk.Euler3DTransform()
            pocetna.SetCenter(fiksni.TransformContinuousIndexToPhysicalPoint(
                [(v - 1) / 2.0 for v in fiksni.GetSize()]))
            tx = _rigidna(fiksni, pokretni, pocetna)
            reg = _na_mrezu(pokretni, fiksni, tx)
            mi_posle = _mi(fiksni, reg)
            info.update(mi_pre=round(mi_pre, 4), mi_posle=round(mi_posle, 4))
            if mi_posle < mi_pre:
                rezultat = reg
                pomeraj, rotacija = _opis(tx)
                info.update(metoda='rigidna (zadržana jer popravlja poravnanje)', primenjena=True,
                            pomeraj_mm=pomeraj, rotacija_step=rotacija)
        except Exception as e:
            info['upozorenje'] = 'Registracija nije uspela ({}).'.format(e)
    sitk.WriteImage(rezultat, str(izlaz_putanja))
    return info
