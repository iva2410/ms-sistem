import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { slika } from '../api';

const RAVNI = [['aksijalni', 'Aksijalni'], ['koronalni', 'Koronalni'], ['sagitalni', 'Sagitalni']];
const OSA = { sagitalni: 0, koronalni: 1, aksijalni: 2 };
// oznake orijentacije: [levo, desno, gore, dole]
const ORIJENTACIJA = {
  aksijalni: ['R', 'L', 'A', 'P'],
  koronalni: ['R', 'L', 'S', 'I'],
  sagitalni: ['A', 'P', 'S', 'I'],
};

function useSlika(putanja) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!putanja) { setUrl(null); return undefined; }
    let vazi = true;
    slika(putanja).then((u) => { if (vazi) setUrl(u); }).catch(() => { if (vazi) setUrl(null); });
    return () => { vazi = false; };
  }, [putanja]);
  return url;
}

function Platno({ prozor, ravan, indeks, ukupno, slojVidljiv, providnost, filter }) {
  const okvir = useRef(null);
  const [prostor, setProstor] = useState({ s: 0, v: 0 });
  const [prirodna, setPrirodna] = useState(null);
  const osnova = useSlika(prozor.osnova(ravan, indeks));
  const sloj = useSlika(slojVidljiv && prozor.sloj ? prozor.sloj(ravan, indeks) : null);

  useLayoutEffect(() => {
    const el = okvir.current;
    const ro = new ResizeObserver(() => setProstor({ s: el.clientWidth, v: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  useEffect(() => { setPrirodna(null); }, [ravan]);

  let stil = { visibility: 'hidden' };
  if (prirodna && prostor.s && prostor.v) {
    const k = Math.min(prostor.s / prirodna.s, prostor.v / prirodna.v);
    stil = { width: Math.floor(prirodna.s * k), height: Math.floor(prirodna.v * k) };
  }
  const [levo, desno, gore, dole] = ORIJENTACIJA[ravan];

  return (
    <div className="platno" ref={okvir}>
      <div className="platno-slika" style={stil}>
        {osnova && (
          <img src={osnova} alt="" draggable={false} style={{ filter }}
            onLoad={(e) => setPrirodna({ s: e.target.naturalWidth, v: e.target.naturalHeight })} />
        )}
        {sloj && <img src={sloj} alt="" draggable={false} className="platno-sloj" style={{ opacity: providnost }} />}
      </div>
      <div className="platno-oznaka gore-levo">
        <strong>{prozor.naslov}</strong>
        {prozor.podnaslov && <span>{prozor.podnaslov}</span>}
      </div>
      <div className="platno-oznaka dole-levo">
        <span>Presek {indeks + 1} / {ukupno}</span>
      </div>
      <span className="platno-strana s-levo">{levo}</span>
      <span className="platno-strana s-desno">{desno}</span>
      <span className="platno-strana s-gore">{gore}</span>
      <span className="platno-strana s-dole">{dole}</span>
    </div>
  );
}

/**
 * Pregledac preseka. prozori: [{ naslov, podnaslov, osnova(ravan, i), sloj(ravan, i) }]
 * lezije: [{ broj, centar: [sag, kor, aks] }] za lenjir; skok: { centar, kljuc } za skok na leziju.
 */
export default function Pregledac({ oblik, prozori, lezije, bojaLezija, imaPouzdanost, skok, vrstaSloja, setVrstaSloja }) {
  const [ravan, setRavan] = useState('aksijalni');
  const [indeksi, setIndeksi] = useState(() => ({
    sagitalni: Math.floor(oblik[0] / 2), koronalni: Math.floor(oblik[1] / 2), aksijalni: Math.floor(oblik[2] / 2),
  }));
  const [slojVidljiv, setSlojVidljiv] = useState(true);
  const [providnost, setProvidnost] = useState(0.55);
  const [osvetljenje, setOsvetljenje] = useState(100);
  const [kontrast, setKontrast] = useState(100);
  const povrsina = useRef(null);

  const ukupno = oblik[OSA[ravan]];
  const indeks = Math.min(indeksi[ravan], ukupno - 1);
  const postavi = (i) => setIndeksi((s) => ({ ...s, [ravan]: Math.max(0, Math.min(ukupno - 1, i)) }));

  // skok na leziju iz tabele: sve tri ravni se postavljaju na centar lezije
  useEffect(() => {
    if (skok) setIndeksi({ sagitalni: skok.centar[0], koronalni: skok.centar[1], aksijalni: skok.centar[2] });
  }, [skok]);

  // tocak misa i strelice listaju preseke
  useEffect(() => {
    const el = povrsina.current;
    const naTocak = (e) => {
      e.preventDefault();
      setIndeksi((s) => ({ ...s, [ravan]: Math.max(0, Math.min(ukupno - 1, s[ravan] + (e.deltaY > 0 ? -1 : 1))) }));
    };
    el.addEventListener('wheel', naTocak, { passive: false });
    return () => el.removeEventListener('wheel', naTocak);
  }, [ravan, ukupno]);

  // susedni preseci se ucitavaju unapred
  useEffect(() => {
    for (const d of [-2, -1, 1, 2]) {
      const i = indeks + d;
      if (i < 0 || i >= ukupno) continue;
      for (const p of prozori) {
        slika(p.osnova(ravan, i)).catch(() => {});
        if (slojVidljiv && p.sloj) slika(p.sloj(ravan, i)).catch(() => {});
      }
    }
  }, [indeks, ravan, ukupno, prozori, slojVidljiv]);

  const preseciSaLezijama = useMemo(
    () => [...new Set((lezije || []).map((l) => l.centar[OSA[ravan]]))].sort((a, b) => a - b),
    [lezije, ravan],
  );
  const sledeca = preseciSaLezijama.find((i) => i > indeks);
  const prethodna = [...preseciSaLezijama].reverse().find((i) => i < indeks);
  const filter = `brightness(${osvetljenje}%) contrast(${kontrast}%)`;

  function naTaster(e) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowRight') { e.preventDefault(); postavi(indeks + 1); }
    if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') { e.preventDefault(); postavi(indeks - 1); }
  }

  return (
    <div className="pregledac">
      <div className="pregledac-alati">
        <div className="segment na-tamnom" role="tablist" aria-label="Ravan preseka">
          {RAVNI.map(([k, naziv]) => (
            <button key={k} role="tab" aria-selected={ravan === k} onClick={() => setRavan(k)}>{naziv}</button>
          ))}
        </div>
        <label className="alat-kvacica">
          <input type="checkbox" checked={slojVidljiv} onChange={(e) => setSlojVidljiv(e.target.checked)} />
          Oznake lezija
        </label>
        {imaPouzdanost && (
          <label className="alat-izbor">
            Prikaz
            <select value={vrstaSloja} onChange={(e) => setVrstaSloja(e.target.value)} disabled={!slojVidljiv}>
              <option value="lezije">Lezije</option>
              <option value="pouzdanost">Mapa pouzdanosti</option>
            </select>
          </label>
        )}
        <label className="alat-klizac">Providnost
          <input type="range" min="0.1" max="1" step="0.05" value={providnost} disabled={!slojVidljiv}
            onChange={(e) => setProvidnost(Number(e.target.value))} />
        </label>
        <label className="alat-klizac">Osvetljenje
          <input type="range" min="50" max="200" value={osvetljenje} onChange={(e) => setOsvetljenje(Number(e.target.value))} />
        </label>
        <label className="alat-klizac">Kontrast
          <input type="range" min="50" max="200" value={kontrast} onChange={(e) => setKontrast(Number(e.target.value))} />
        </label>
        {(osvetljenje !== 100 || kontrast !== 100) && (
          <button className="dugme-tiho na-tamnom" onClick={() => { setOsvetljenje(100); setKontrast(100); }}>Vrati prikaz</button>
        )}
      </div>

      <div className={`pregledac-platna broj-${prozori.length}`} ref={povrsina} tabIndex={0} onKeyDown={naTaster}
        aria-label="Preseci snimka. Strelice ili točak miša listaju preseke.">
        {prozori.map((p) => (
          <Platno key={p.naslov} prozor={p} ravan={ravan} indeks={indeks} ukupno={ukupno}
            slojVidljiv={slojVidljiv} providnost={providnost} filter={filter} />
        ))}
      </div>

      <div className="lenjir">
        <button className="dugme-tiho na-tamnom" disabled={prethodna === undefined} onClick={() => postavi(prethodna)}>
          Prethodna lezija
        </button>
        <div className="lenjir-traka">
          <div className="lenjir-oznake" aria-hidden="true">
            {preseciSaLezijama.map((i) => (
              <span key={i} style={{ left: `${ukupno > 1 ? (i / (ukupno - 1)) * 100 : 50}%`, background: bojaLezija }} />
            ))}
          </div>
          <input type="range" min="0" max={ukupno - 1} value={indeks} onChange={(e) => postavi(Number(e.target.value))}
            aria-label="Presek" />
        </div>
        <button className="dugme-tiho na-tamnom" disabled={sledeca === undefined} onClick={() => postavi(sledeca)}>
          Sledeća lezija
        </button>
      </div>
    </div>
  );
}
