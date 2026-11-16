import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, putanje, slika } from '../api';
import { Greska } from '../delovi/Zajednicko';
import { POL, REGION, broj, datum, datumVreme, godine } from '../pomocne';

function KljucniPresek({ snimakId, analizaId, lezija, opis }) {
  const [osnova, setOsnova] = useState(null);
  const [sloj, setSloj] = useState(null);
  const i = lezija.centar[2];
  useEffect(() => {
    slika(putanje.presek(snimakId, 'aksijalni', i)).then(setOsnova).catch(() => {});
    slika(putanje.sloj(analizaId, 'lezije', 'aksijalni', i)).then(setSloj).catch(() => {});
  }, [snimakId, analizaId, i]);
  if (!osnova) return null;
  return (
    <figure className="izv-slika">
      <div>
        <img src={osnova} alt="" />
        {sloj && <img src={sloj} alt="" className="platno-sloj" />}
      </div>
      <figcaption>{opis}, aksijalni presek {i + 1}</figcaption>
    </figure>
  );
}

function TabelaLezija({ lezije }) {
  return (
    <table className="izv-tabela">
      <thead>
        <tr><th>Br.</th><th>Zapremina (mm³)</th><th>Aksijalni presek</th><th>Pouzdanost detekcije</th></tr>
      </thead>
      <tbody>
        {lezije.map((l) => (
          <tr key={l.broj}>
            <td>{l.broj}</td><td>{broj(l.zapremina_mm3, 1)}</td><td>{l.centar[2] + 1}</td>
            <td>{Math.round(l.pouzdanost * 100)}% ({l.kategorija})</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Izvestaj() {
  const { id } = useParams();
  const [iz, setIz] = useState(null);
  const [pregled, setPregled] = useState(null);
  const [tekst, setTekst] = useState('');
  const [greska, setGreska] = useState('');
  const [poruka, setPoruka] = useState('');

  const primi = useCallback((d) => { setIz(d); setTekst(d.zakljucak || ''); }, []);
  useEffect(() => {
    Promise.all([api.izvestaj(id), api.pregled(id)])
      .then(([d, p]) => { primi(d); setPregled(p); })
      .catch((g) => setGreska(g.message));
  }, [id, primi]);

  if (greska && !iz) return <main className="strana"><Greska poruka={greska} /></main>;
  if (!iz || !pregled) return <main className="strana" />;

  const potvrdjen = iz.status === 'potvrdjen';
  const pac = iz.pacijent;
  const glavni = pregled.snimci.find((s) => s.sekvenca === 'FLAIR' || s.sekvenca === 'T2');
  const najveca = (r) => (r?.lezije.length ? [...r.lezije].sort((a, b) => b.zapremina_mm3 - a.zapremina_mm3)[0] : null);

  async function uradi(akcija, potvrda) {
    setGreska(''); setPoruka('');
    try { primi(await akcija()); setPoruka(potvrda); } catch (g) { setGreska(g.message); }
  }

  return (
    <main className="strana izv-strana">
      <div className="ne-stampaj">
        <p className="putanja">
          <Link to="/">Radna lista</Link> / <Link to={`/pacijenti/${pac.id}`}>{pac.prezime} {pac.ime}</Link> /{' '}
          <Link to={`/pregledi/${id}`}>Pregled {datum(iz.datum_snimanja)}</Link> / Izveštaj
        </p>
        <div className="strana-glava">
          <h1>Izveštaj</h1>
          <div className="strana-alati">
            {poruka && <span className="potvrda" role="status">{poruka}</span>}
            {iz.spreman && !potvrdjen && (
              <>
                <button className="dugme-tiho" onClick={() => setTekst(iz.predlog_zakljucka)}>Vrati predloženi tekst</button>
                <button className="dugme-tiho" onClick={() => uradi(() => api.sacuvajIzvestaj(id, tekst), 'Nacrt je sačuvan.')}>Sačuvaj nacrt</button>
                <button className="dugme-glavno" onClick={() => uradi(() => api.potvrdiIzvestaj(id, tekst), 'Izveštaj je potvrđen.')}>Potvrdi izveštaj</button>
              </>
            )}
            {potvrdjen && (
              <>
                <button className="dugme-tiho" onClick={() => uradi(() => api.otvoriIzvestaj(id), 'Izveštaj je otvoren za izmenu.')}>Otvori za izmenu</button>
                <button className="dugme-glavno" onClick={() => window.print()}>Štampaj ili sačuvaj kao PDF</button>
              </>
            )}
          </div>
        </div>
        <Greska poruka={greska} />
        {!iz.spreman && <div className="prazno"><p>Izveštaj se formira kada se analiza snimka završi.</p></div>}
        {iz.spreman && !potvrdjen && (
          <p className="bledo">Proverite nalaz, po potrebi izmenite zaključak i potvrdite izveštaj. Štampa je dostupna posle potvrde.</p>
        )}
      </div>

      {iz.spreman && (
        <article className={`izv ${potvrdjen ? '' : 'izv-nacrt'}`}>
          <header className="izv-glava">
            <div>
              <p className="izv-ustanova">{iz.lekar?.ustanova || 'Zdravstvena ustanova nije uneta'}</p>
              <h2>Izveštaj o analizi MR snimka</h2>
              <p>{REGION[iz.region]}, sekvence {iz.sekvence.join(' + ')}</p>
            </div>
            <div className="izv-oznaka">
              <p>Pregled br. {iz.pregled_id}</p>
              <p>{potvrdjen ? `Potvrđen ${datumVreme(iz.potvrdjen)}` : 'Nacrt, nije potvrđen'}</p>
            </div>
          </header>

          <dl className="izv-podaci">
            <div><dt>Pacijent</dt><dd>{pac.prezime} {pac.ime}</dd></div>
            <div><dt>Broj kartona</dt><dd>{pac.broj_kartona || 'nije unet'}</dd></div>
            <div><dt>Datum rođenja</dt><dd>{pac.datum_rodjenja ? `${datum(pac.datum_rodjenja)} (${godine(pac.datum_rodjenja, iz.datum_snimanja)} god.)` : 'nije unet'}</dd></div>
            <div><dt>Pol</dt><dd>{POL[pac.pol] || 'nije unet'}</dd></div>
            <div><dt>Datum snimanja</dt><dd>{datum(iz.datum_snimanja)}</dd></div>
            <div><dt>Prethodni pregled</dt><dd>{iz.prethodni ? datum(iz.prethodni.datum_snimanja) : 'nema'}</dd></div>
          </dl>

          <section>
            <h3>Nalaz</h3>
            <table className="izv-tabela izv-zbir">
              <thead>
                <tr><th></th><th>Broj lezija</th><th>Ukupna zapremina (ml)</th><th>Najveća lezija (mm³)</th><th>Niske pouzdanosti</th></tr>
              </thead>
              <tbody>
                <tr>
                  <th>Sve lezije</th><td>{iz.sve.broj_lezija}</td><td>{broj(iz.sve.zapremina_ml, 2)}</td>
                  <td>{broj(iz.sve.najveca_mm3)}</td><td>{iz.sve.niska_pouzdanost}</td>
                </tr>
                {iz.prethodni?.broj_lezija != null && (
                  <tr>
                    <th>Prethodni pregled ({datum(iz.prethodni.datum_snimanja)})</th>
                    <td>{iz.prethodni.broj_lezija}</td><td>{broj(iz.prethodni.zapremina_ml, 2)}</td><td></td><td></td>
                  </tr>
                )}
                {iz.nove && (
                  <tr>
                    <th>Nove lezije u odnosu na prethodni pregled</th><td>{iz.nove.broj_lezija}</td>
                    <td>{broj(iz.nove.zapremina_ml, 2)}</td><td>{broj(iz.nove.najveca_mm3)}</td><td>{iz.nove.niska_pouzdanost}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>

          {iz.nove && iz.nove.lezije.length > 0 && (
            <section>
              <h3>Nove lezije</h3>
              <TabelaLezija lezije={iz.nove.lezije} />
            </section>
          )}
          {iz.sve.lezije.length > 0 && (
            <section>
              <h3>Sve lezije</h3>
              <TabelaLezija lezije={iz.sve.lezije} />
            </section>
          )}

          {glavni && (najveca(iz.sve) || najveca(iz.nove)) && (
            <section className="izv-slike">
              {najveca(iz.nove) && pregled.analize.nove_lezije && (
                <KljucniPresek snimakId={glavni.id} analizaId={pregled.analize.nove_lezije.id} lezija={najveca(iz.nove)}
                  opis={`Najveća nova lezija (br. ${najveca(iz.nove).broj})`} />
              )}
              {najveca(iz.sve) && pregled.analize.sve_lezije && (
                <KljucniPresek snimakId={glavni.id} analizaId={pregled.analize.sve_lezije.id} lezija={najveca(iz.sve)}
                  opis={`Najveća lezija (br. ${najveca(iz.sve).broj})`} />
              )}
            </section>
          )}

          <section>
            <h3>Zaključak</h3>
            {potvrdjen
              ? <p className="izv-zakljucak">{iz.zakljucak}</p>
              : <textarea className="izv-unos" rows={6} value={tekst} onChange={(e) => { setTekst(e.target.value); setPoruka(''); }}
                  aria-label="Zaključak" />}
          </section>

          <section>
            <h3>Postupak analize</h3>
            {iz.tehnika.map((t) => <p key={t} className="izv-sitno">{t}</p>)}
            <p className="izv-sitno">
              Pouzdanost detekcije je srednja vrednost izlaza modela unutar lezije i nije kalibrisana verovatnoća.
            </p>
          </section>

          <footer className="izv-dno">
            <p className="izv-napomena">{iz.napomena}</p>
            <div className="izv-potpis">
              <p>{iz.lekar?.puno_ime}</p>
              <p>{[iz.lekar?.specijalnost, iz.lekar?.broj_licence && `licenca ${iz.lekar.broj_licence}`].filter(Boolean).join(', ')}</p>
            </div>
          </footer>
        </article>
      )}
    </main>
  );
}
