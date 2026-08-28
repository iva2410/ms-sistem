import { useState } from 'react';
import './stil.css';
import Pacijenti from './Pacijenti';
import Analiza from './Analiza';
import Karton from './Karton';

export default function App() {
  const [tab, setTab] = useState('pacijenti');
  const [izabran, setIzabran] = useState(null);

  return (
    <div className="app">
      <div className="header">
        <h1>🧠 Sistem za analizu lezija multiple skleroze</h1>
        <p>Automatska detekcija, merenje i radiološki nalaz na osnovu MR snimka mozga</p>
      </div>

      <div className="tabovi">
        <div className={`tab ${tab === 'pacijenti' ? 'aktivan' : ''}`} onClick={() => setTab('pacijenti')}>
          Pacijenti
        </div>
        <div className={`tab ${tab === 'analiza' ? 'aktivan' : ''}`} onClick={() => setTab('analiza')}>
          Analiza
        </div>
        <div className={`tab ${tab === 'karton' ? 'aktivan' : ''}`} onClick={() => setTab('karton')}>
          Karton pacijenta
        </div>
      </div>

      {tab === 'pacijenti' && <Pacijenti izabran={izabran} postaviIzabranog={setIzabran} />}
      {tab === 'analiza' && <Analiza izabran={izabran} />}
      {tab === 'karton' && <Karton izabran={izabran} />}
    </div>
  );
}