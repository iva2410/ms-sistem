export function datum(iso) {
  if (!iso) return '';
  const [g, m, d] = iso.slice(0, 10).split('-');
  return `${d}.${m}.${g}.`;
}

export function datumVreme(iso) {
  if (!iso) return '';
  return `${datum(iso)} u ${iso.slice(11, 16)}`;
}

export function godine(isoRodjenja, naDan) {
  if (!isoRodjenja) return null;
  const r = new Date(isoRodjenja);
  const d = naDan ? new Date(naDan) : new Date();
  let g = d.getFullYear() - r.getFullYear();
  if (d.getMonth() < r.getMonth() || (d.getMonth() === r.getMonth() && d.getDate() < r.getDate())) g -= 1;
  return g;
}

export function broj(v, decimala = 0) {
  if (v === null || v === undefined) return '';
  return Number(v).toLocaleString('sr-Latn-RS', { minimumFractionDigits: decimala, maximumFractionDigits: decimala });
}

export const REGION = { mozak: 'Mozak', kicma: 'Kičmena moždina' };
export const POL = { M: 'muški', Z: 'ženski', '': '' };
export const STANJE = {
  u_toku: 'Analiza u toku',
  za_pregled: 'Čeka pregled lekara',
  potvrdjen: 'Izveštaj potvrđen',
  greska: 'Greška u analizi',
  bez_analize: 'Bez analize',
};
export const POUZDANOST = { visoka: 'visoka', srednja: 'srednja', niska: 'niska' };

export function danas() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
