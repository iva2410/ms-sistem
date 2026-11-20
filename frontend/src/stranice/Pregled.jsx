import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, putanje } from '../api';
import Pregledac from '../delovi/Pregledac';
import { Dijalog, Greska, Stanje } from '../delovi/Zajednicko';
import { REGION, broj, datum, godine } from '../pomocne';

const NAZIV_ANALIZE = { sve_lezije: 'Detekcija lezija', nove_lezije: 'Poređenje sa prethodnim snimkom' };
const BOJA = { sve: '#FFB000', nove: '#FF3D8B' };

function Tok({ analize, ponovi }) {
  const aktivne = analize.filter((a) => a.status !== 'zavrsena');
  if (!aktivne.length) return null;
  return (
    <section className="tok">
      {aktivne.map((a) => (
        <div key={a.id} className="tok-stavka">
          <div className="tok-red">
            <strong>{NAZIV_ANALIZE[a.tip]}</strong>
            <span>{a.status === 'greska' ? 'Analiza nije uspela' : a.korak}</span>
          </div>
          {a.status === 'greska' ? (
            <>
              <p className="poruka-greska">{a.greska}</p>
              <button className="dugme-tiho" onClick={() => ponovi(a.id)}>Pokreni analizu ponovo</button>
            </>
          ) : (
            <div className="napredak" role="progressbar" aria-valuenow={a.napredak} aria-valuemin={0} aria-valuemax={100}>
              <div style={{ width: `${Math.max(3, a.napredak)}%` }} />
            </div>
          )}
        </div>
      ))}
      {aktivne.some((a) => a.status !== 'greska') && (
        <p className="bledo">
          Na računaru bez grafičke kartice analiza može trajati deset i više minuta. Stranicu možete zatvoriti, analiza se nastavlja.
        </p>
      )}
    </section>
  );
}

function Tehnika({ t }) {
  const reg = t.registracija;
  return (
    <details className="tehnika">
      <summary>Podaci o analizi</summary>
      <dl>
        <div><dt>Model</dt><dd>{t.model}</dd></div>
        <div><dt>Ulaz</dt><dd>{t.ulaz}</dd></div>
        {reg && <div><dt>Poravnanje</dt><dd>
          {reg.metoda}{reg.primenjena && reg.pomeraj_mm != null ? `: pomeraj ${broj(reg.pomeraj_mm, 1)} mm, rotacija ${broj(reg.rotacija_step, 1)}°` : ''}
        </dd></div>}
      </dl>
      {reg?.upozorenje && <p className="poruka-upozorenje">{reg.upozorenje}</p>}
      {t.napomena && <p className="poruka-upozorenje">{t.napomena}</p>}
    </details>
  );
}

export default function Pregled() {
  const { id } = useParams();
  const idi = useNavigate();
  const [p, setP] = useState(null);
  const [greska, setGreska] = useState('');
  const [rezim, setRezim] = useState(null);       // 'sve' | 'nove'
  const [vrstaSloja, setVrstaSloja] = useState('lezije');
  const [skok, setSkok] = useState(null);
  const [izabrana, setIzabrana] = useState(null);
  const [brisanje, setBrisanje] = useState(false);

  const ucitaj = useCallback(() => api.pregled(id).then(setP).catch((g) => setGreska(g.message)), [id]);
  useEffect(() => { setP(null); setRezim(null); ucitaj(); }, [ucitaj]);
  useEffect(() => {
    if (p?.stanje !== 'u_toku') return undefined;
    const t = setInterval(ucitaj, 2500);
    return () => clearInterval(t);
  }, [p, ucitaj]);

  const sve = p?.analize.sve_lezije;
  const nove = p?.analize.nove_lezije;
  const imaNove = nove?.status === 'zavrsena';
  const aktivan = rezim === 'nove' && imaNove ? 'nove' : rezim === 'sve' ? 'sve' : imaNove ? 'nove' : 'sve';
  const analiza = aktivan === 'nove' ? nove : sve;
  const rez = analiza?.status === 'zavrsena' ? analiza.rezultati : null;
  const glavni = p?.snimci.find((s) => s.sekvenca === 'FLAIR' || s.sekvenca === 'T2');

  const prozori = useMemo(() => {
    if (!glavni) return [];
    const sloj = rez ? (ravan, i) => putanje.sloj(analiza.id, vrstaSloja, ravan, i) : null;
    const noviji = {
      naslov: aktivan === 'nove' ? 'Noviji snimak' : glavni.sekvenca,
      podnaslov: datum(p.datum_snimanja),
      osnova: (ravan, i) => putanje.presek(glavni.id, ravan, i),
      sloj,
    };
    if (aktivan === 'nove' && rez) {
      return [{
        naslov: 'Raniji snimak',
        podnaslov: `${datum(rez.prethodni_datum)}, poravnat sa novijim`,
        osnova: (ravan, i) => putanje.raniji(analiza.id, ravan, i),
        sloj: null,
      }, noviji];
    }
    return [noviji];
  }, [glavni, rez, analiza, aktivan, vrstaSloja, p]);

  if (greska && !p) return <main className="strana"><Greska poruka={greska} /></main>;
  if (!p) return <main className="strana" />;

  const pac = p.pacijent;
  const analize = Object.values(p.analize);

  async function ponovi(aid) {
    try { await api.ponoviAnalizu(aid); ucitaj(); } catch (g) { setGreska(g.message); }
  }
  async function obrisi() {
    try { await api.obrisiPregled(p.id); idi(`/pacijenti/${pac.id}`); } catch (g) { setGreska(g.message); setBrisanje(false); }
  }

  return (
    <main className="pregled">
      <div className="pregled-glava">
        <div>
          <p className="putanja">
            <Link to="/">Radna lista</Link> / <Link to={`/pacijenti/${pac.id}`}>{pac.prezime} {pac.ime}</Link> / Pregled
          </p>
          <h1>{REGION[p.region]}, {datum(p.datum_snimanja)}</h1>
          <dl className="podaci-red">
            <div><dt>Pacijent</dt><dd>{pac.prezime} {pac.ime}{pac.datum_rodjenja ? `, ${godine(pac.datum_rodjenja, p.datum_snimanja)} god.` : ''}</dd></div>
            <div><dt>Sekvence</dt><dd>{p.snimci.map((s) => s.sekvenca).join(' + ')}</dd></div>
            {p.prethodni && <div><dt>Prethodni pregled</dt><dd><Link to={`/pregledi/${p.prethodni.id}`}>{datum(p.prethodni.datum_snimanja)}</Link></dd></div>}
            <div><dt>Stanje</dt><dd><Stanje stanje={p.stanje} /></dd></div>
          </dl>
        </div>
        <div className="strana-alati">
          <button className="dugme-tiho" onClick={() => setBrisanje(true)}>Obriši pregled</button>
          <Link className="dugme-glavno" to={`/pregledi/${p.id}/izvestaj`}>Izveštaj</Link>
        </div>
      </div>
      <Greska poruka={greska} />

      <div className="pregled-telo">
        <div className="pregled-levo">
          {glavni?.oblik ? (
            <Pregledac key={`${glavni.id}-${aktivan}`} oblik={glavni.oblik} prozori={prozori}
              lezije={rez?.lezije} bojaLezija={BOJA[aktivan]} imaPouzdanost={!!rez}
              skok={skok} vrstaSloja={vrstaSloja} setVrstaSloja={setVrstaSloja} />
          ) : (
            <div className="prazno"><p>Snimak ne može da se prikaže{glavni?.greska ? `: ${glavni.greska}` : '.'}</p></div>
          )}
        </div>

        <aside className="pregled-desno">
          <Tok analize={analize} ponovi={ponovi} />

          {imaNove && sve?.status === 'zavrsena' && (
            <div className="segment segment-pun" role="tablist" aria-label="Vrsta nalaza">
              <button role="tab" aria-selected={aktivan === 'nove'} onClick={() => { setRezim('nove'); setIzabrana(null); }}>
                Nove lezije ({nove.rezultati.broj_lezija})
              </button>
              <button role="tab" aria-selected={aktivan === 'sve'} onClick={() => { setRezim('sve'); setIzabrana(null); }}>
                Sve lezije ({sve.rezultati.broj_lezija})
              </button>
            </div>
          )}

          {rez && (
            <>
              <dl className="mere">
                <div><dt>{aktivan === 'nove' ? 'Novih lezija' : 'Lezija'}</dt><dd>{rez.broj_lezija}</dd></div>
                <div><dt>Ukupna zapremina</dt><dd>{broj(rez.zapremina_ml, 2)} <small>ml</small></dd></div>
                <div><dt>Najveća</dt><dd>{broj(rez.najveca_mm3)} <small>mm³</small></dd></div>
                <div><dt>Niske pouzdanosti</dt><dd>{rez.niska_pouzdanost}</dd></div>
              </dl>
              {aktivan === 'sve' && p.prethodni?.broj_lezija != null && (
                <p className="poredjenje">
                  Prethodni pregled ({datum(p.prethodni.datum_snimanja)}): {p.prethodni.broj_lezija} lezija,{' '}
                  {broj(p.prethodni.zapremina_ml, 2)} ml.
                </p>
              )}
              {aktivan === 'nove' && rez.broj_lezija === 0 && (
                <p className="nalaz-stabilan">U poređenju sa snimkom od {datum(rez.prethodni_datum)} nisu detektovane nove lezije.</p>
              )}

              {rez.lezije.length > 0 && (
                <div className="lezije-okvir">
                  <table className="tabela tabela-klik tabela-zbijena">
                    <thead>
                      <tr><th>Br.</th><th className="desno">Zapremina (mm³)</th><th className="desno">Presek</th><th>Pouzdanost</th></tr>
                    </thead>
                    <tbody>
                      {rez.lezije.map((l) => (
                        <tr key={l.broj} className={izabrana === l.broj ? 'izabran' : ''} tabIndex={0}
                          onClick={() => { setIzabrana(l.broj); setSkok({ centar: l.centar, kljuc: `${aktivan}-${l.broj}` }); }}
                          onKeyDown={(e) => { if (e.key === 'Enter') { setIzabrana(l.broj); setSkok({ centar: l.centar, kljuc: `${aktivan}-${l.broj}` }); } }}>
                          <td>{l.broj}</td>
                          <td className="desno">{broj(l.zapremina_mm3, 1)}</td>
                          <td className="desno">{l.centar[2] + 1}</td>
                          <td>
                            <span className={`pouzdanost pouzdanost-${l.kategorija}`}>
                              <span className="pouzdanost-traka"><span style={{ width: `${Math.round(l.pouzdanost * 100)}%` }} /></span>
                              {Math.round(l.pouzdanost * 100)}% {l.kategorija}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="bledo malo">
                Izaberite leziju da je prikažete na snimku. Pouzdanost je srednja vrednost izlaza modela unutar lezije i nije
                kalibrisana verovatnoća; detekcije niske pouzdanosti treba proveriti.
              </p>
              <Tehnika t={rez.tehnika} />
            </>
          )}
          {p.napomena && <p className="karton-napomena">{p.napomena}</p>}
        </aside>
      </div>

      {brisanje && (
        <Dijalog naslov="Brisanje pregleda" zatvori={() => setBrisanje(false)}>
          <div className="dijalog-telo">
            <p>Pregled od {datum(p.datum_snimanja)} biće obrisan zajedno sa snimcima i rezultatima analize. Ovo se ne može poništiti.</p>
            <div className="dijalog-dugmad">
              <button className="dugme-tiho" onClick={() => setBrisanje(false)}>Odustani</button>
              <button className="dugme-opasno" onClick={obrisi}>Obriši pregled</button>
            </div>
          </div>
        </Dijalog>
      )}
    </main>
  );
}
