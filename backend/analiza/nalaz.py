"""Strukturiran radioloski izvestaj: podaci i predlog teksta zakljucka."""
import json

NAPOMENA = ('Nalaz je formiran automatskom analizom MR snimka i služi kao pomoć lekaru. '
            'Ne predstavlja dijagnozu niti preporuku terapije; konačnu procenu donosi lekar '
            'na osnovu celokupne kliničke slike.')

_REGION = {'mozak': 'mozga', 'kicma': 'kičmene moždine'}


def _datum(d):
    return d.strftime('%d.%m.%Y.') if d else ''


def _lezija_oblik(n):
    if n % 10 == 1 and n % 100 != 11:
        return 'lezija'
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return 'lezije'
    return 'lezija'


def rezultati(analiza):
    if analiza is None or analiza.status != 'zavrsena' or not analiza.rezultati:
        return None
    return json.loads(analiza.rezultati)


def analiza_tipa(pregled, tip):
    kandidati = [a for a in pregled.analize if a.tip == tip]
    return kandidati[-1] if kandidati else None


def predlog_zakljucka(pregled, sve, nove, prethodni_pregled, prethodni_sve):
    """Recenice koje lekar moze da prihvati ili izmeni."""
    delovi = []
    if sve:
        n = sve['broj_lezija']
        if n == 0:
            delovi.append('Automatskom analizom MR snimka {} nisu detektovane lezije.'.format(
                _REGION[pregled.region]))
        else:
            delovi.append(
                'Automatskom analizom MR snimka {} detektovano je {} {} ukupne zapremine {} ml; '
                'najveća lezija ima {} mm³.'.format(
                    _REGION[pregled.region], n, _lezija_oblik(n),
                    str(sve['zapremina_ml']).replace('.', ','),
                    str(round(sve['najveca_mm3'])).replace('.', ',')))
            if sve.get('niska_pouzdanost'):
                delovi.append('Detekcija niske pouzdanosti: {} (zahtevaju proveru).'.format(
                    sve['niska_pouzdanost']))
    if nove:
        n = nove['broj_lezija']
        dat = _datum(prethodni_pregled.datum_snimanja) if prethodni_pregled else ''
        if n == 0:
            delovi.append('U poređenju sa snimkom od {} nisu detektovane nove lezije; na osnovu ovog '
                          'poređenja nema radioloških znakova aktivnosti bolesti.'.format(dat))
        else:
            delovi.append('U poređenju sa snimkom od {} detektovano je {} novih lezija (ukupno {} mm³), '
                          'što odgovara radiološkim znacima aktivnosti bolesti. Preporučuje se klinička '
                          'korelacija.'.format(dat, n, str(round(nove['zapremina_mm3'])).replace('.', ',')))
    elif sve and prethodni_sve and prethodni_pregled:
        delovi.append('U odnosu na pregled od {}: broj lezija {} → {}, ukupna zapremina {} → {} ml.'.format(
            _datum(prethodni_pregled.datum_snimanja), prethodni_sve['broj_lezija'], sve['broj_lezija'],
            str(prethodni_sve['zapremina_ml']).replace('.', ','), str(sve['zapremina_ml']).replace('.', ',')))
    return ' '.join(delovi)


def tehnika_redovi(sve, nove):
    redovi = []
    for naziv, r in (('Detekcija lezija', sve), ('Detekcija novih lezija', nove)):
        if not r:
            continue
        t = r['tehnika']
        red = '{}: {} — ulaz {}; {}.'.format(naziv, t.get('model', ''), t.get('ulaz', ''), t.get('uredjaj', ''))
        reg = t.get('registracija')
        if reg:
            red += ' Poravnanje: {}'.format(reg.get('metoda', ''))
            if reg.get('pomeraj_mm') is not None and reg.get('primenjena'):
                red += ' (pomeraj {} mm, rotacija {}°)'.format(
                    str(reg['pomeraj_mm']).replace('.', ','), str(reg['rotacija_step']).replace('.', ','))
            red += '.'
            if reg.get('upozorenje'):
                red += ' ' + reg['upozorenje']
        if t.get('napomena'):
            red += ' ' + t['napomena']
        redovi.append(red)
    return redovi
