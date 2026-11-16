import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import PacijentForma from '../delovi/PacijentForma';
import { Greska, Stanje } from '../delovi/Zajednicko';
import { REGION, datum, godine } from '../pomocne';

export default function RadnaLista() {
  const [lista, setLista] = useState(null);
  const [pretraga, setPretraga] = useState('');
  const [greska, setGreska] = useState('');
  const [forma, setForma] = useState(false);
  const idi = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => {
      api.pacijenti(pretraga).then(setLista).catch((g) => setGreska(g.message));
    }, pretraga ? 250 : 0);
    return () => clearTimeout(t);
  }, [pretraga]);

  return (
    <main className="strana">
      <div className="strana-glava">
        <h1>Radna lista</h1>
        <div className="strana-alati">
          <input
            type="search" className="pretraga" placeholder="Pretraga po imenu, prezimenu ili broju kartona"
            value={pretraga} onChange={(e) => setPretraga(e.target.value)} aria-label="Pretraga pacijenata"
          />
          <button className="dugme-glavno" onClick={() => setForma(true)}>Novi pacijent</button>
        </div>
      </div>
      <Greska poruka={greska} />

      {lista && lista.length === 0 && (
        <div className="prazno">
          {pretraga
            ? <p>Nijedan pacijent ne odgovara pretrazi „{pretraga}”.</p>
            : <><p>Još nema unetih pacijenata.</p><p>Dodajte pacijenta da biste učitali prvi snimak.</p></>}
        </div>
      )}

      {lista && lista.length > 0 && (
        <table className="tabela tabela-klik">
          <thead>
            <tr>
              <th>Pacijent</th><th>Broj kartona</th><th>Datum rođenja</th>
              <th className="desno">Pregleda</th><th>Poslednji pregled</th><th>Stanje</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((p) => (
              <tr key={p.id} onClick={() => idi(`/pacijenti/${p.id}`)} tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter') idi(`/pacijenti/${p.id}`); }}>
                <td className="jako">{p.prezime} {p.ime}</td>
                <td>{p.broj_kartona || <span className="bledo">nije unet</span>}</td>
                <td>{p.datum_rodjenja ? `${datum(p.datum_rodjenja)} (${godine(p.datum_rodjenja)} god.)` : ''}</td>
                <td className="desno">{p.broj_pregleda}</td>
                <td>{p.poslednji_pregled
                  ? `${datum(p.poslednji_pregled.datum_snimanja)} ${REGION[p.poslednji_pregled.region].toLowerCase()}`
                  : <span className="bledo">nema pregleda</span>}</td>
                <td>{p.poslednji_pregled && <Stanje stanje={p.poslednji_pregled.stanje} />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {forma && <PacijentForma zatvori={() => setForma(false)} sacuvano={(p) => idi(`/pacijenti/${p.id}`)} />}
    </main>
  );
}
