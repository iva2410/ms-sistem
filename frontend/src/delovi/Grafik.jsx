import { broj, datum } from '../pomocne';

// Linijski grafik jedne velicine kroz vreme (SVG, bez spoljnih biblioteka).
export default function Grafik({ tacke, polje, naziv, jedinica, decimala = 0, izaberi }) {
  const S = 520, V = 190, L = 44, D = 16, G = 16, DOLE = 34;
  const vrednosti = tacke.map((t) => t[polje]);
  const maks = Math.max(1, ...vrednosti) * 1.15;
  const vremena = tacke.map((t) => new Date(t.datum).getTime());
  const t0 = Math.min(...vremena), t1 = Math.max(...vremena);
  const x = (i) => (t1 === t0 ? L + (S - L - D) / 2 : L + ((vremena[i] - t0) / (t1 - t0)) * (S - L - D));
  const y = (v) => G + (1 - v / maks) * (V - G - DOLE);
  const podeoci = [0, maks / 2 / 1.15, maks / 1.15];
  const putanja = tacke.map((t, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(t[polje]).toFixed(1)}`).join(' ');

  return (
    <figure className="grafik">
      <figcaption>{naziv}{jedinica ? ` (${jedinica})` : ''}</figcaption>
      <svg viewBox={`0 0 ${S} ${V}`} role="img" aria-label={`${naziv} kroz vreme`}>
        {podeoci.map((p, i) => (
          <g key={i}>
            <line x1={L} x2={S - D} y1={y(p)} y2={y(p)} className="grafik-mreza" />
            <text x={L - 8} y={y(p) + 4} textAnchor="end" className="grafik-osa">{broj(p, decimala)}</text>
          </g>
        ))}
        <path d={putanja} className="grafik-linija" />
        {tacke.map((t, i) => (
          <g key={t.pregled_id} className="grafik-tacka" onClick={() => izaberi?.(t.pregled_id)}>
            <title>{`${datum(t.datum)} ${broj(t[polje], decimala)}${jedinica ? ` ${jedinica}` : ''}`}</title>
            <circle cx={x(i)} cy={y(t[polje])} r="11" fill="transparent" />
            <circle cx={x(i)} cy={y(t[polje])} r="4" />
            <text x={tacke.length > 1 && i === 0 ? x(i) + 8 : x(i)} y={y(t[polje]) - 10}
              textAnchor={tacke.length > 1 && i === 0 ? 'start' : tacke.length > 1 && i === tacke.length - 1 ? 'end' : 'middle'} className="grafik-vrednost">{broj(t[polje], decimala)}</text>
            {polje === 'broj_lezija' && t.nove_lezije > 0 && (
              <text x={x(i)} y={y(t[polje]) + 20} textAnchor="middle" className="grafik-nove">+{t.nove_lezije} novih</text>
            )}
            <text x={x(i)} y={V - 10} textAnchor={tacke.length > 1 && i === 0 ? 'start' : tacke.length > 1 && i === tacke.length - 1 ? 'end' : 'middle'}
              className="grafik-osa">{datum(t.datum)}</text>
          </g>
        ))}
      </svg>
    </figure>
  );
}
