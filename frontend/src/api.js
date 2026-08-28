import axios from 'axios';

const API = 'http://localhost:8000';

export async function dodajPacijenta(ime, datumRodjenja) {
  const fd = new FormData();
  fd.append('ime', ime);
  fd.append('datum_rodjenja', datumRodjenja);
  const r = await axios.post(`${API}/pacijent`, fd);
  return r.data;
}

export async function sviPacijenti() {
  const r = await axios.get(`${API}/pacijenti`);
  return r.data;
}

export async function istorijaPacijenta(pid) {
  const r = await axios.get(`${API}/pacijent/${pid}/istorija`);
  return r.data;
}

export async function analizaPrvi(pacijentId, snimak) {
  const fd = new FormData();
  fd.append('pacijent_id', pacijentId);
  fd.append('snimak', snimak);
  const r = await axios.post(`${API}/analiza/prvi`, fd);
  return r.data;
}

export async function analizaKontrola(pacijentId, snimak) {
  const fd = new FormData();
  fd.append('pacijent_id', pacijentId);
  fd.append('snimak', snimak);
  const r = await axios.post(`${API}/analiza/kontrola`, fd);
  return r.data;
}