import { useState, useEffect } from 'react';
import { istorijaPacijenta } from './api';

export default function Karton({ izabran }) {
  const [istorija, setIstorija] = useState([]);

  useEffect(() => {
    if (izabran) {
      istorijaPacijenta(izabran).then(setIstorija);
    } else {
      setIstorija([]);
    }
  }, [izabran]);

  if (!izabran) {
    return <div className="kartica"><p>Izaberite pacijenta u tabu Pacijenti.</p></div>;
  }

  return (
    <div className="kartica">
      <div className="sekcija-naslov">Karton pacijenta</div>
      <p style={{ marginBottom: 16 }}>Ukupno pregleda: <b>{istorija.length}</b></p>

      {istorija.length === 0 && <p style={{ color: '#64748b' }}>Još nema pregleda za ovog pacijenta.</p>}

      {istorija.map(pr => (
        <div key={pr.id} className="kartica" style={{ background: '#f8fafc', marginBottom: 12 }}>
          <p style={{ color: '#1a5a9e', fontWeight: 600 }}>
            {pr.tip === 'prvi' ? 'Prvi pregled (sve lezije)' : 'Kontrolni pregled (nove lezije)'} — {pr.datum}
          </p>
          <div style={{ marginTop: 8 }}>
            {pr.tip === 'prvi' ? (
              <>
                <p>Broj lezija: <b>{pr.rezultati.broj_lezija}</b></p>
                <p>Ukupna zapremina: <b>{pr.rezultati.zapremina_ml} mL</b></p>
                <p>Najveća lezija: <b>{pr.rezultati.najveca_ml} mL</b></p>
              </>
            ) : (
              <>
                <p>Broj novih lezija: <b>{pr.rezultati.broj_novih_lezija}</b></p>
                <p>Zapremina novih lezija: <b>{pr.rezultati.zapremina_novih_ml} mL</b></p>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}