import { useState } from 'react';
import { analizaPrvi, analizaKontrola } from './api';

export default function Analiza({ izabran }) {
  const [tip, setTip] = useState('prvi');
  const [snimak, setSnimak] = useState(null);
  const [rezultat, setRezultat] = useState(null);
  const [ucitavanje, setUcitavanje] = useState(false);
  const [greska, setGreska] = useState('');

  async function analiziraj() {
    if (!izabran) { setGreska('Prvo izaberite pacijenta.'); return; }
    if (!snimak) { setGreska('Učitajte snimak.'); return; }
    setGreska(''); setUcitavanje(true); setRezultat(null);
    try {
      const r = tip === 'prvi'
        ? await analizaPrvi(izabran, snimak)
        : await analizaKontrola(izabran, snimak);
      setRezultat(r);
    } catch (e) {
      setGreska(e.response?.data?.detail || 'Greška pri analizi.');
    }
    setUcitavanje(false);
  }

  return (
    <div className="kartica">
      <div className="sekcija-naslov">Analiza snimka</div>

      {!izabran && <p style={{ color: '#dc2626' }}>Izaberite pacijenta u tabu Pacijenti.</p>}

      <label>Tip pregleda:</label>
      <select value={tip} onChange={e => { setTip(e.target.value); setRezultat(null); }}>
        <option value="prvi">Prvi pregled (sve lezije)</option>
        <option value="kontrola">Kontrolni pregled (nove lezije)</option>
      </select>

      {tip === 'kontrola' && (
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 6 }}>
          Učitajte samo novi snimak — sistem će ga uporediti sa prethodnim iz kartona.
        </p>
      )}

      <label style={{ display: 'block', marginTop: 12 }}>
        {tip === 'prvi' ? 'FLAIR snimak:' : 'Novi FLAIR snimak:'}
      </label>
      <input type="file" accept=".nii,.gz" onChange={e => setSnimak(e.target.files[0])} />

      <button onClick={analiziraj} disabled={ucitavanje}>
        {ucitavanje ? 'Analiziram...' : 'Analiziraj'}
      </button>

      {greska && <p style={{ color: '#dc2626', marginTop: 10 }}>{greska}</p>}

      {rezultat && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            <img className="presek" src={rezultat.slika} alt="presek" style={{ maxWidth: 380 }} />
            <div style={{ flex: 1 }}>
              <div className="metrike" style={{ flexDirection: 'column' }}>
                {tip === 'prvi' ? (
                  <>
                    <div className="metrika"><div className="metrika-broj">{rezultat.broj_lezija}</div><div className="metrika-opis">Broj lezija</div></div>
                    <div className="metrika"><div className="metrika-broj">{rezultat.zapremina_ml} mL</div><div className="metrika-opis">Ukupna zapremina</div></div>
                    <div className="metrika"><div className="metrika-broj">{rezultat.najveca_ml} mL</div><div className="metrika-opis">Najveća lezija</div></div>
                  </>
                ) : (
                  <>
                    <div className="metrika"><div className="metrika-broj">{rezultat.broj_novih_lezija}</div><div className="metrika-opis">Broj novih lezija</div></div>
                    <div className="metrika"><div className="metrika-broj">{rezultat.zapremina_novih_ml} mL</div><div className="metrika-opis">Zapremina novih lezija</div></div>
                  </>
                )}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="sekcija-naslov" style={{ fontSize: 17 }}>Radiološki nalaz</div>
            {rezultat.nalaz.aktivnost && (
              <div className={rezultat.nalaz.aktivnost.includes('Nema') ? 'nalaz-stabilan' : 'nalaz-aktivan'}>
                {rezultat.nalaz.aktivnost}
              </div>
            )}
            {rezultat.nalaz.radioloski_nalaz && <p style={{ marginTop: 8 }}><b>{rezultat.nalaz.radioloski_nalaz}</b></p>}
            {rezultat.nalaz.lezijsko_opterecenje && <p style={{ marginTop: 8 }}>Lezijsko opterećenje: {rezultat.nalaz.lezijsko_opterecenje}</p>}
            <p className="napomena">{rezultat.nalaz.napomena}</p>
          </div>
        </div>
      )}
    </div>
  );
}