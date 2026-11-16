// Komunikacija sa serverom. Adresa se moze promeniti promenljivom VITE_API.
const API = import.meta.env.VITE_API || 'http://localhost:8000';
const KLJUC = 'ms-prijava';

let naIstekPrijave = () => {};
export function postaviIstekPrijave(f) { naIstekPrijave = f; }

export function sacuvanaPrijava() {
  try { return JSON.parse(sessionStorage.getItem(KLJUC)); } catch { return null; }
}
export function zapamtiPrijavu(p) {
  if (p) sessionStorage.setItem(KLJUC, JSON.stringify(p));
  else sessionStorage.removeItem(KLJUC);
}

function zaglavlja() {
  const p = sacuvanaPrijava();
  return p?.token ? { Authorization: `Bearer ${p.token}` } : {};
}

async function odgovor(r) {
  if (r.status === 401 && sacuvanaPrijava()) naIstekPrijave();
  if (!r.ok) {
    let poruka = 'Server nije odgovorio kako treba. Pokušajte ponovo.';
    try {
      const d = (await r.json()).detail;
      if (typeof d === 'string') poruka = d;
      else if (Array.isArray(d)) poruka = 'Proverite unete podatke.';
    } catch { /* odgovor nije JSON */ }
    const g = new Error(poruka);
    g.status = r.status;
    throw g;
  }
  return r;
}

async function zahtev(metoda, putanja, telo) {
  const opcije = { method: metoda, headers: zaglavlja() };
  if (telo instanceof FormData) opcije.body = telo;
  else if (telo !== undefined) {
    opcije.headers['Content-Type'] = 'application/json';
    opcije.body = JSON.stringify(telo);
  }
  let r;
  try {
    r = await fetch(API + putanja, opcije);
  } catch {
    throw new Error('Server nije dostupan. Proverite da li je backend pokrenut.');
  }
  return (await odgovor(r)).json();
}

export const api = {
  registracija: (p) => zahtev('POST', '/nalog/registracija', p),
  prijava: (p) => zahtev('POST', '/nalog/prijava', p),
  izmeniProfil: (p) => zahtev('PUT', '/nalog/ja', p),
  pacijenti: (pretraga) => zahtev('GET', `/pacijenti?pretraga=${encodeURIComponent(pretraga || '')}`),
  dodajPacijenta: (p) => zahtev('POST', '/pacijenti', p),
  izmeniPacijenta: (id, p) => zahtev('PUT', `/pacijenti/${id}`, p),
  karton: (id) => zahtev('GET', `/pacijenti/${id}`),
  pracenje: (id) => zahtev('GET', `/pacijenti/${id}/pracenje`),
  noviPregled: (fd) => zahtev('POST', '/pregledi', fd),
  pregled: (id) => zahtev('GET', `/pregledi/${id}`),
  obrisiPregled: (id) => zahtev('DELETE', `/pregledi/${id}`),
  ponoviAnalizu: (id) => zahtev('POST', `/analize/${id}/ponovi`),
  izvestaj: (id) => zahtev('GET', `/pregledi/${id}/izvestaj`),
  sacuvajIzvestaj: (id, zakljucak) => zahtev('PUT', `/pregledi/${id}/izvestaj`, { zakljucak }),
  potvrdiIzvestaj: (id, zakljucak) => zahtev('POST', `/pregledi/${id}/izvestaj/potvrdi`, { zakljucak }),
  otvoriIzvestaj: (id) => zahtev('POST', `/pregledi/${id}/izvestaj/otvori`),
  sistem: () => zahtev('GET', '/sistem'),
};

// ---- preseci: slike se preuzimaju sa prijavom i cuvaju u memoriji ----
const kes = new Map();
const MAKS_SLIKA = 500;

export function slika(putanja) {
  if (kes.has(putanja)) return kes.get(putanja);
  const obecanje = fetch(API + putanja, { headers: zaglavlja() })
    .then(odgovor)
    .then((r) => r.blob())
    .then((b) => URL.createObjectURL(b));
  kes.set(putanja, obecanje);
  obecanje.catch(() => kes.delete(putanja));
  if (kes.size > MAKS_SLIKA) {
    const [stara, staroObecanje] = kes.entries().next().value;
    kes.delete(stara);
    staroObecanje.then((u) => URL.revokeObjectURL(u)).catch(() => {});
  }
  return obecanje;
}

export const putanje = {
  presek: (snimakId, ravan, i) => `/snimci/${snimakId}/presek?ravan=${ravan}&i=${i}`,
  sloj: (analizaId, vrsta, ravan, i) => `/analize/${analizaId}/sloj?vrsta=${vrsta}&ravan=${ravan}&i=${i}`,
  raniji: (analizaId, ravan, i) => `/analize/${analizaId}/raniji?ravan=${ravan}&i=${i}`,
};
