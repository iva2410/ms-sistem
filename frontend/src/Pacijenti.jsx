import { useState, useEffect } from 'react';
import { sviPacijenti, dodajPacijenta } from './api';

export default function Pacijenti({ izabran, postaviIzabranog }) {
  const [lista, setLista] = useState([]);
  const [ime, setIme] = useState('');
  const [datum, setDatum] = useState('');

  async function ucitaj() {
    setLista(await sviPacijenti());
  }
  useEffect(() => { ucitaj(); }, []);

  async function dodaj() {
    if (!ime.trim()) return;
    const novi = await dodajPacijenta(ime, datum);
    setIme(''); setDatum('');
    await ucitaj();
    postaviIzabranog(novi.id);
  }

  return (
    <div className="kartica">
      <div className="sekcija-naslov">Pacijenti</div>
      <label>Izaberi pacijenta:</label>
      <select value={izabran || ''} onChange={e => postaviIzabranog(Number(e.target.value))}>
        <option value="">-- izaberi --</option>
        {lista.map(p => <option key={p.id} value={p.id}>{p.ime}</option>)}
      </select>

      <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #e2e8f0' }}>
        <label>Dodaj novog pacijenta:</label>
        <input placeholder="Ime i prezime" value={ime} onChange={e => setIme(e.target.value)} />
        <input placeholder="Datum rođenja (npr. 15.03.1985)" value={datum} onChange={e => setDatum(e.target.value)} />
        <button onClick={dodaj}>Dodaj pacijenta</button>
      </div>
    </div>
  );
}