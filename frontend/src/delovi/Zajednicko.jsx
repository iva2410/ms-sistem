import { useEffect } from 'react';
import { STANJE } from '../pomocne';

export function Stanje({ stanje }) {
  return <span className={`stanje stanje-${stanje}`}>{STANJE[stanje] || stanje}</span>;
}

export function Greska({ poruka }) {
  if (!poruka) return null;
  return <p className="poruka-greska" role="alert">{poruka}</p>;
}

export function Polje({ naziv, pomoc, children }) {
  return (
    <label className="polje">
      <span className="polje-naziv">{naziv}</span>
      {children}
      {pomoc && <span className="polje-pomoc">{pomoc}</span>}
    </label>
  );
}

export function Dijalog({ naslov, zatvori, children, sirok }) {
  useEffect(() => {
    const naTaster = (e) => { if (e.key === 'Escape') zatvori(); };
    window.addEventListener('keydown', naTaster);
    return () => window.removeEventListener('keydown', naTaster);
  }, [zatvori]);
  return (
    <div className="dijalog-pozadina" onMouseDown={(e) => { if (e.target === e.currentTarget) zatvori(); }}>
      <div className={`dijalog ${sirok ? 'dijalog-sirok' : ''}`} role="dialog" aria-modal="true" aria-label={naslov}>
        <div className="dijalog-glava">
          <h2>{naslov}</h2>
          <button className="dugme-tiho" onClick={zatvori} aria-label="Zatvori">Zatvori</button>
        </div>
        {children}
      </div>
    </div>
  );
}
