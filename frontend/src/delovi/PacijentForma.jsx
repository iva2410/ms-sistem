import { useState } from 'react';
import { api } from '../api';
import { Dijalog, Greska, Polje } from './Zajednicko';

export default function PacijentForma({ pacijent, zatvori, sacuvano }) {
  const [p, setP] = useState({
    ime: pacijent?.ime || '', prezime: pacijent?.prezime || '', broj_kartona: pacijent?.broj_kartona || '',
    datum_rodjenja: pacijent?.datum_rodjenja || '', pol: pacijent?.pol || '', napomena: pacijent?.napomena || '',
  });
  const [greska, setGreska] = useState('');
  const [ceka, setCeka] = useState(false);
  const polje = (k) => ({ value: p[k], onChange: (e) => setP({ ...p, [k]: e.target.value }) });

  async function posalji(e) {
    e.preventDefault();
    setCeka(true);
    setGreska('');
    try {
      const podaci = { ...p, datum_rodjenja: p.datum_rodjenja || null };
      sacuvano(pacijent ? await api.izmeniPacijenta(pacijent.id, podaci) : await api.dodajPacijenta(podaci));
    } catch (g) {
      setGreska(g.message);
      setCeka(false);
    }
  }

  return (
    <Dijalog naslov={pacijent ? 'Podaci o pacijentu' : 'Novi pacijent'} zatvori={zatvori}>
      <form onSubmit={posalji} className="dijalog-telo">
        <div className="red-polja">
          <Polje naziv="Ime"><input {...polje('ime')} required autoFocus /></Polje>
          <Polje naziv="Prezime"><input {...polje('prezime')} required /></Polje>
        </div>
        <div className="red-polja">
          <Polje naziv="Broj kartona"><input {...polje('broj_kartona')} /></Polje>
          <Polje naziv="Datum rođenja"><input type="date" {...polje('datum_rodjenja')} /></Polje>
          <Polje naziv="Pol">
            <select {...polje('pol')}>
              <option value="">nije uneto</option>
              <option value="Z">ženski</option>
              <option value="M">muški</option>
            </select>
          </Polje>
        </div>
        <Polje naziv="Napomena"><textarea rows={3} {...polje('napomena')} /></Polje>
        <Greska poruka={greska} />
        <div className="dijalog-dugmad">
          <button type="button" className="dugme-tiho" onClick={zatvori}>Odustani</button>
          <button className="dugme-glavno" disabled={ceka}>{pacijent ? 'Sačuvaj izmene' : 'Dodaj pacijenta'}</button>
        </div>
      </form>
    </Dijalog>
  );
}
