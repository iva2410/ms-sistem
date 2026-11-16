import { NavLink, Outlet } from 'react-router-dom';
import { useNalog } from '../App';

export default function Okvir() {
  const { lekar, odjavi } = useNalog();
  return (
    <div className="okvir">
      <header className="traka ne-stampaj">
        <NavLink to="/" className="traka-naziv">
          <svg viewBox="0 0 32 32" width="22" height="22" aria-hidden="true">
            <circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
            <circle cx="20" cy="12.5" r="3" fill="#FFB000" />
          </svg>
          MS sistem
        </NavLink>
        <nav className="traka-nav">
          <NavLink to="/" end>Radna lista</NavLink>
          <NavLink to="/podesavanja">Podešavanja</NavLink>
        </nav>
        <div className="traka-lekar">
          <span>
            {lekar.puno_ime}
            {lekar.ustanova && <small>{lekar.ustanova}</small>}
          </span>
          <button className="dugme-tiho na-tamnom" onClick={odjavi}>Odjavi se</button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
