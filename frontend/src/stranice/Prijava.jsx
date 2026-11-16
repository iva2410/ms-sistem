import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useNalog } from '../App';
import { Greska, Polje } from '../delovi/Zajednicko';

const PRAZNO = { email: '', lozinka: '', lozinka2: '', ime: '', prezime: '', titula: 'dr', specijalnost: '', ustanova: '', broj_licence: '' };

export default function Prijava({ nacin }) {
  const { prijavi } = useNalog();
  const [p, setP] = useState(PRAZNO);
  const [greska, setGreska] = useState('');
  const [ceka, setCeka] = useState(false);
  const reg = nacin === 'registracija';
  const polje = (k) => ({ value: p[k], onChange: (e) => setP({ ...p, [k]: e.target.value }) });

  async function posalji(e) {
    e.preventDefault();
    setGreska('');
    if (reg && p.lozinka.length < 8) return setGreska('Lozinka mora imati najmanje 8 znakova.');
    if (reg && p.lozinka !== p.lozinka2) return setGreska('Lozinke se ne poklapaju.');
    setCeka(true);
    try {
      const { lozinka2, ...podaci } = p;
      prijavi(reg ? await api.registracija(podaci) : await api.prijava({ email: p.email, lozinka: p.lozinka }));
    } catch (g) {
      setGreska(g.message);
      setCeka(false);
    }
  }

  return (
    <div className="ulaz">
      <section className="ulaz-opis">
        <div className="ulaz-znak">
          <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
            <circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
            <circle cx="20" cy="12.5" r="3" fill="#FFB000" />
          </svg>
          MS sistem
        </div>
        <h1>Analiza i praćenje lezija multiple skleroze na MR snimcima mozga i kičmene moždine</h1>
        <ul>
          <li>Detekcija i merenje lezija na pojedinačnom snimku</li>
          <li>Poređenje kontrolnog snimka sa prethodnim i izdvajanje novih lezija</li>
          <li>Praćenje broja i zapremine lezija kroz vreme</li>
          <li>Strukturiran izveštaj koji lekar pregleda, menja i potvrđuje</li>
        </ul>
        <p className="ulaz-napomena">
          Sistem je pomoć lekaru pri očitavanju snimaka. Ne postavlja dijagnozu i ne predlaže terapiju.
        </p>
      </section>

      <section className="ulaz-forma">
        <form onSubmit={posalji}>
          <h2>{reg ? 'Registracija lekara' : 'Prijava'}</h2>
          {reg && (
            <>
              <div className="red-polja">
                <Polje naziv="Titula"><input {...polje('titula')} placeholder="dr, prof. dr" /></Polje>
                <Polje naziv="Ime"><input {...polje('ime')} required autoComplete="given-name" /></Polje>
                <Polje naziv="Prezime"><input {...polje('prezime')} required autoComplete="family-name" /></Polje>
              </div>
              <Polje naziv="Specijalnost"><input {...polje('specijalnost')} placeholder="npr. radiologija, neurologija" /></Polje>
              <Polje naziv="Zdravstvena ustanova"><input {...polje('ustanova')} /></Polje>
              <Polje naziv="Broj licence"><input {...polje('broj_licence')} /></Polje>
            </>
          )}
          <Polje naziv="Adresa e-pošte"><input type="email" {...polje('email')} required autoComplete="email" /></Polje>
          <Polje naziv="Lozinka" pomoc={reg ? 'Najmanje 8 znakova.' : null}>
            <input type="password" {...polje('lozinka')} required autoComplete={reg ? 'new-password' : 'current-password'} />
          </Polje>
          {reg && (
            <Polje naziv="Ponovite lozinku">
              <input type="password" {...polje('lozinka2')} required autoComplete="new-password" />
            </Polje>
          )}
          <Greska poruka={greska} />
          <button className="dugme-glavno dugme-siroko" disabled={ceka}>
            {reg ? 'Registruj nalog' : 'Prijavi se'}
          </button>
          <p className="ulaz-zamena">
            {reg
              ? <>Već imate nalog? <Link to="/">Prijavite se</Link></>
              : <>Nemate nalog? <Link to="/registracija">Registrujte se</Link></>}
          </p>
        </form>
      </section>
    </div>
  );
}
