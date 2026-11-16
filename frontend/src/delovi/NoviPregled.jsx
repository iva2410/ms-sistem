import { useState } from 'react';
import { api } from '../api';
import { danas } from '../pomocne';
import { Dijalog, Greska, Polje } from './Zajednicko';

export default function NoviPregled({ pacijent, imaRanijiMozak, zatvori, napravljen }) {
  const [region, setRegion] = useState('mozak');
  const [datumSnimanja, setDatumSnimanja] = useState(danas());
  const [flair, setFlair] = useState(null);
  const [t2, setT2] = useState(null);
  const [dodatna, setDodatna] = useState(null);
  const [vrstaDodatne, setVrstaDodatne] = useState('STIR');
  const [napomena, setNapomena] = useState('');
  const [greska, setGreska] = useState('');
  const [ceka, setCeka] = useState(false);

  async function posalji(e) {
    e.preventDefault();
    setGreska('');
    const fd = new FormData();
    fd.append('pacijent_id', pacijent.id);
    fd.append('region', region);
    fd.append('datum_snimanja', datumSnimanja);
    fd.append('napomena', napomena);
    if (region === 'mozak') {
      if (!flair) return setGreska('Izaberite FLAIR snimak.');
      fd.append('flair', flair);
    } else {
      if (!t2) return setGreska('Izaberite T2 snimak.');
      if (!dodatna) return setGreska(`Izaberite ${vrstaDodatne} snimak.`);
      fd.append('t2', t2);
      fd.append('dodatna', dodatna);
      fd.append('dodatna_sekvenca', vrstaDodatne);
    }
    setCeka(true);
    try {
      napravljen((await api.noviPregled(fd)).id);
    } catch (g) {
      setGreska(g.message);
      setCeka(false);
    }
  }

  return (
    <Dijalog naslov={`Novi pregled: ${pacijent.prezime} ${pacijent.ime}`} zatvori={zatvori}>
      <form onSubmit={posalji} className="dijalog-telo">
        <fieldset className="izbor">
          <legend>Region</legend>
          <label><input type="radio" name="region" checked={region === 'mozak'} onChange={() => setRegion('mozak')} /> Mozak</label>
          <label><input type="radio" name="region" checked={region === 'kicma'} onChange={() => setRegion('kicma')} /> Kičmena moždina</label>
        </fieldset>
        <Polje naziv="Datum snimanja">
          <input type="date" value={datumSnimanja} max={danas()} onChange={(e) => setDatumSnimanja(e.target.value)} required />
        </Polje>

        {region === 'mozak' ? (
          <Polje naziv="FLAIR snimak (.nii ili .nii.gz)"
            pomoc={imaRanijiMozak
              ? 'Snimak će biti upoređen sa prethodnim pregledom mozga radi otkrivanja novih lezija.'
              : 'Prvi pregled mozga: detektuju se i mere sve lezije.'}>
            <input type="file" accept=".nii,.gz" onChange={(e) => setFlair(e.target.files[0] || null)} />
          </Polje>
        ) : (
          <>
            <Polje naziv="T2 snimak (.nii ili .nii.gz)">
              <input type="file" accept=".nii,.gz" onChange={(e) => setT2(e.target.files[0] || null)} />
            </Polje>
            <div className="red-polja">
              <Polje naziv="Druga sekvenca">
                <select value={vrstaDodatne} onChange={(e) => setVrstaDodatne(e.target.value)}>
                  <option>STIR</option><option>PSIR</option><option>MP2RAGE</option>
                </select>
              </Polje>
              <Polje naziv={`${vrstaDodatne} snimak (.nii ili .nii.gz)`} pomoc="Analiza koristi obe sekvence zajedno.">
                <input type="file" accept=".nii,.gz" onChange={(e) => setDodatna(e.target.files[0] || null)} />
              </Polje>
            </div>
          </>
        )}
        <Polje naziv="Napomena"><textarea rows={2} value={napomena} onChange={(e) => setNapomena(e.target.value)} /></Polje>
        <Greska poruka={greska} />
        <div className="dijalog-dugmad">
          <button type="button" className="dugme-tiho" onClick={zatvori}>Odustani</button>
          <button className="dugme-glavno" disabled={ceka}>{ceka ? 'Učitavanje snimaka…' : 'Učitaj i pokreni analizu'}</button>
        </div>
      </form>
    </Dijalog>
  );
}
