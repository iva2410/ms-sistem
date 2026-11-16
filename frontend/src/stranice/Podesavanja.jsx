import { useEffect, useState } from 'react';
import { api } from '../api';
import { useNalog } from '../App';
import { Greska, Polje } from '../delovi/Zajednicko';

export default function Podesavanja() {
  const { lekar, osveziLekara } = useNalog();
  const [p, setP] = useState({
    titula: lekar.titula, ime: lekar.ime, prezime: lekar.prezime, specijalnost: lekar.specijalnost,
    ustanova: lekar.ustanova, broj_licence: lekar.broj_licence,
  });
  const [sistem, setSistem] = useState(null);
  const [greska, setGreska] = useState('');
  const [sacuvano, setSacuvano] = useState(false);
  const polje = (k) => ({ value: p[k], onChange: (e) => { setP({ ...p, [k]: e.target.value }); setSacuvano(false); } });

  useEffect(() => { api.sistem().then(setSistem).catch((g) => setGreska(g.message)); }, []);

  async function sacuvaj(e) {
    e.preventDefault();
    setGreska('');
    try {
      osveziLekara(await api.izmeniProfil(p));
      setSacuvano(true);
    } catch (g) { setGreska(g.message); }
  }

  return (
    <main className="strana strana-uska">
      <div className="strana-glava"><h1>Podešavanja</h1></div>

      <section>
        <h2>Podaci o lekaru</h2>
        <p className="bledo">Ovi podaci se upisuju u zaglavlje i potpis izveštaja.</p>
        <form onSubmit={sacuvaj} className="forma-blok">
          <div className="red-polja">
            <Polje naziv="Titula"><input {...polje('titula')} /></Polje>
            <Polje naziv="Ime"><input {...polje('ime')} required /></Polje>
            <Polje naziv="Prezime"><input {...polje('prezime')} required /></Polje>
          </div>
          <div className="red-polja">
            <Polje naziv="Specijalnost"><input {...polje('specijalnost')} /></Polje>
            <Polje naziv="Broj licence"><input {...polje('broj_licence')} /></Polje>
          </div>
          <Polje naziv="Zdravstvena ustanova"><input {...polje('ustanova')} /></Polje>
          <Polje naziv="Adresa e-pošte"><input value={lekar.email} disabled /></Polje>
          <Greska poruka={greska} />
          <div className="dijalog-dugmad">
            {sacuvano && <span className="potvrda" role="status">Izmene su sačuvane.</span>}
            <button className="dugme-glavno">Sačuvaj izmene</button>
          </div>
        </form>
      </section>

      <section>
        <h2>Modeli za analizu</h2>
        {sistem && (
          <>
            <p className="bledo">Analiza se izvršava na: {sistem.uredjaj}. Modeli se čitaju iz foldera backend/modeli.</p>
            <table className="tabela">
              <thead><tr><th>Model</th><th>Folder</th><th>Stanje</th></tr></thead>
              <tbody>
                {sistem.modeli.map((m) => (
                  <tr key={m.kljuc}>
                    <td className="jako">{m.opis}</td>
                    <td>{m.folder}</td>
                    <td>{m.instaliran
                      ? <span className="stanje stanje-potvrdjen">Instaliran</span>
                      : <span className="stanje stanje-greska">Nije pronađen</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
    </main>
  );
}
