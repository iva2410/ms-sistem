import { createContext, useContext, useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { postaviIstekPrijave, sacuvanaPrijava, zapamtiPrijavu } from './api';
import Okvir from './delovi/Okvir';
import Prijava from './stranice/Prijava';
import RadnaLista from './stranice/RadnaLista';
import Karton from './stranice/Karton';
import Pregled from './stranice/Pregled';
import Izvestaj from './stranice/Izvestaj';
import Podesavanja from './stranice/Podesavanja';

const Nalog = createContext(null);
export const useNalog = () => useContext(Nalog);

export default function App() {
  const [prijava, setPrijava] = useState(sacuvanaPrijava);

  function postavi(p) {
    zapamtiPrijavu(p);
    setPrijava(p);
  }
  useEffect(() => { postaviIstekPrijave(() => postavi(null)); }, []);

  const vrednost = {
    lekar: prijava?.lekar || null,
    prijavi: postavi,
    odjavi: () => postavi(null),
    osveziLekara: (lekar) => postavi({ ...prijava, lekar }),
  };

  return (
    <Nalog.Provider value={vrednost}>
      {!prijava ? (
        <Routes>
          <Route path="/registracija" element={<Prijava nacin="registracija" />} />
          <Route path="*" element={<Prijava nacin="prijava" />} />
        </Routes>
      ) : (
        <Routes>
          <Route element={<Okvir />}>
            <Route path="/" element={<RadnaLista />} />
            <Route path="/pacijenti/:id" element={<Karton />} />
            <Route path="/pregledi/:id" element={<Pregled />} />
            <Route path="/pregledi/:id/izvestaj" element={<Izvestaj />} />
            <Route path="/podesavanja" element={<Podesavanja />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      )}
    </Nalog.Provider>
  );
}
