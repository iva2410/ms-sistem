import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api';
import Grafik from '../delovi/Grafik';
import NoviPregled from '../delovi/NoviPregled';
import PacijentForma from '../delovi/PacijentForma';
import { Greska, Stanje } from '../delovi/Zajednicko';
import { POL, REGION, broj, datum, godine } from '../pomocne';

export default function Karton() {
  const { id } = useParams();
  const idi = useNavigate();
  const [p, setP] = useState(null);
  const [tok, setTok] = useState(null);
  const [region, setRegion] = useState(null);
  const [greska, setGreska] = useState('');
  const [forma, setForma] = useState(null);   // 'pacijent' | 'pregled'

  const ucitaj = useCallback(() => {
    Promise.all([api.karton(id), api.pracenje(id)])
      .then(([k, t]) => { setP(k); setTok(t); })
      .catch((g) => setGreska(g.message));
  }, [id]);
  useEffect(ucitaj, [ucitaj]);

  // dok neka analiza traje, karton se povremeno osvezava
  useEffect(() => {
    if (!p?.pregledi.some((x) => x.stanje === 'u_toku')) return undefined;
    const t = setInterval(ucitaj, 4000);
    return () => clearInterval(t);
  }, [p, ucitaj]);

  if (greska) return <main className="strana"><Greska poruka={greska} /></main>;
  if (!p) return <main className="strana" />;

  const regioni = ['mozak', 'kicma'].filter((r) => tok[r].length > 0);
  const prikazan = regioni.includes(region) ? region : regioni[0];

  return (
    <main className="strana">
      <p className="putanja"><Link to="/">Radna lista</Link> / Karton pacijenta</p>
      <div className="strana-glava">
        <div>
          <h1>{p.prezime} {p.ime}</h1>
          <dl className="podaci-red">
            <div><dt>Broj kartona</dt><dd>{p.broj_kartona || 'nije unet'}</dd></div>
            <div><dt>Datum rođenja</dt><dd>{p.datum_rodjenja ? `${datum(p.datum_rodjenja)} (${godine(p.datum_rodjenja)} god.)` : 'nije unet'}</dd></div>
            <div><dt>Pol</dt><dd>{POL[p.pol] || 'nije unet'}</dd></div>
          </dl>
          {p.napomena && <p className="karton-napomena">{p.napomena}</p>}
        </div>
        <div className="strana-alati">
          <button className="dugme-tiho" onClick={() => setForma('pacijent')}>Izmeni podatke</button>
          <button className="dugme-glavno" onClick={() => setForma('pregled')}>Novi pregled</button>
        </div>
      </div>

      <div className="karton-mreza">
        <section>
          <h2>Pregledi</h2>
          {p.pregledi.length === 0 ? (
            <div className="prazno">
              <p>Pacijent još nema pregleda.</p>
              <p>Izaberite „Novi pregled” i učitajte MR snimak.</p>
            </div>
          ) : (
            <table className="tabela tabela-klik">
              <thead>
                <tr>
                  <th>Datum snimanja</th><th>Region</th><th>Sekvence</th>
                  <th className="desno">Lezija</th><th className="desno">Zapremina (ml)</th>
                  <th className="desno">Novih</th><th>Stanje</th>
                </tr>
              </thead>
              <tbody>
                {p.pregledi.map((x) => (
                  <tr key={x.id} onClick={() => idi(`/pregledi/${x.id}`)} tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter') idi(`/pregledi/${x.id}`); }}>
                    <td className="jako">{datum(x.datum_snimanja)}</td>
                    <td>{REGION[x.region]}</td>
                    <td>{x.sekvence.join(' + ')}</td>
                    <td className="desno">{x.broj_lezija ?? ''}</td>
                    <td className="desno">{x.zapremina_ml !== null ? broj(x.zapremina_ml, 2) : ''}</td>
                    <td className="desno">{x.nove_lezije ?? ''}</td>
                    <td><Stanje stanje={x.stanje} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section>
          <div className="naslov-red">
            <h2>Praćenje kroz vreme</h2>
            {regioni.length > 1 && (
              <div className="segment" role="tablist">
                {regioni.map((r) => (
                  <button key={r} role="tab" aria-selected={prikazan === r} onClick={() => setRegion(r)}>{REGION[r]}</button>
                ))}
              </div>
            )}
          </div>
          {!prikazan ? (
            <div className="prazno"><p>Grafik se prikazuje kada se završi analiza bar jednog pregleda.</p></div>
          ) : (
            <>
              {regioni.length === 1 && <p className="bledo">{REGION[prikazan]}</p>}
              <Grafik tacke={tok[prikazan]} polje="broj_lezija" naziv="Broj lezija" izaberi={(pid) => idi(`/pregledi/${pid}`)} />
              <Grafik tacke={tok[prikazan]} polje="zapremina_ml" naziv="Ukupna zapremina lezija" jedinica="ml" decimala={2}
                izaberi={(pid) => idi(`/pregledi/${pid}`)} />
            </>
          )}
        </section>
      </div>

      {forma === 'pacijent' && (
        <PacijentForma pacijent={p} zatvori={() => setForma(null)} sacuvano={() => { setForma(null); ucitaj(); }} />
      )}
      {forma === 'pregled' && (
        <NoviPregled pacijent={p} imaRanijiMozak={p.pregledi.some((x) => x.region === 'mozak')}
          zatvori={() => setForma(null)} napravljen={(pid) => idi(`/pregledi/${pid}`)} />
      )}
    </main>
  );
}
