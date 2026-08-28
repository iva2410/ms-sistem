def klinicki_nalaz_nov_pacijent(broj_lezija, zapremina_mm3, najveca_mm3, prosek_skupa=None):
    """Nalaz za novog pacijenta (jedan snimak, sve lezije)."""
    zapremina_ml = zapremina_mm3 / 1000  # mm3 u mL
    najveca_ml = najveca_mm3 / 1000

    nalaz = {
        'tip': 'Prvi pregled (detekcija svih lezija)',
        'broj_lezija': broj_lezija,
        'ukupna_zapremina_ml': round(zapremina_ml, 2),
        'najveca_lezija_ml': round(najveca_ml, 2),
    }

    # lezijsko opterecenje - RELATIVNO (posteno, bez izmisljenih apsolutnih pragova)
    if prosek_skupa is not None:
        if zapremina_ml < prosek_skupa * 0.5:
            opterecenje = 'nisko (ispod proseka analiziranih pacijenata)'
        elif zapremina_ml < prosek_skupa * 1.5:
            opterecenje = 'umereno (oko proseka analiziranih pacijenata)'
        else:
            opterecenje = 'visoko (iznad proseka analiziranih pacijenata)'
        nalaz['lezijsko_opterecenje'] = opterecenje

    nalaz['napomena'] = ('Automatski nalaz zasnovan na analizi MR snimka. '
                         'Ne predstavlja dijagnozu. Klinicku procenu donosi lekar.')
    return nalaz


def klinicki_nalaz_kontrola(nove_lezije_broj, nove_lezije_mm3):
    """Nalaz za kontrolni pregled (poredjenje dva snimka - nove lezije)."""
    nove_ml = nove_lezije_mm3 / 1000

    nalaz = {
        'tip': 'Kontrolni pregled (poredjenje sa prethodnim snimkom)',
        'broj_novih_lezija': nove_lezije_broj,
        'zapremina_novih_ml': round(nove_ml, 2),
    }

    # NEDA koncept - klinicki cvrsto (pojava novih lezija = znak aktivnosti)
    if nove_lezije_broj == 0:
        nalaz['radioloski_nalaz'] = 'Bez novih lezija - radioloski stabilno'
        nalaz['aktivnost'] = 'Nema radioloskih znakova aktivnosti bolesti'
    else:
        nalaz['radioloski_nalaz'] = f'Detektovano {nove_lezije_broj} novih lezija'
        nalaz['aktivnost'] = ('Prisutni radioloski znaci aktivnosti bolesti. '
                              'Preporucuje se klinicka korelacija.')

    nalaz['napomena'] = ('Automatski nalaz. Odluku o terapiji i daljem pracenju '
                         'donosi lekar na osnovu celokupne klinicke slike.')
    return nalaz
