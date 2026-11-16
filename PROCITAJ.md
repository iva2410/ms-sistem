# MS sistem

Aplikacija za detekciju i praćenje lezija multiple skleroze na MR snimcima mozga i kičmene moždine.
Backend: FastAPI + PostgreSQL + nnU-Net. Frontend: React + Vite.

## Prvo pokretanje

1. **Baza** (jednom). U pgAdmin-u ili psql-u: `CREATE DATABASE ms_sistem;`
   Ako baza `ms_sistem` već postoji, ne treba ništa; tabele (`ms_lekar`, `ms_pacijent`, ...) prave se same.
   Ako korisnik ili lozinka nisu `postgres` / `postgres`, kopiraj `backend/env_primer.txt` u `backend/.env` i izmeni `MS_BAZA_URL`.

2. **Backend** (u folderu `backend`):

       pip install -r requirements.txt
       uvicorn main:app --port 8000

3. **Frontend** (u folderu `frontend`, drugi terminal):

       npm install
       npm run dev

   Aplikacija je na http://localhost:5173. Prvo se registruje lekar, zatim prijava.

4. **Modeli.** Preuzmi ih sa Drive-a u `backend/modeli` prema uputstvu u `backend/modeli/PROCITAJ.txt`.
   Stranica „Podešavanja” pokazuje koji su modeli pronađeni. Bez modela sve radi osim same analize
   (analiza prijavi koji model nedostaje i može se ponoviti kada se model doda).

## Šta aplikacija radi

- registracija i prijava lekara; podaci lekara idu u zaglavlje i potpis izveštaja
- radna lista pacijenata, karton pacijenta sa svim pregledima
- mozak (FLAIR) i kičmena moždina (T2 zajedno sa STIR, PSIR ili MP2RAGE)
- prvi pregled: detekcija i merenje svih lezija
- kontrolni pregled mozga: raniji snimak se poravnava sa novijim (rigidna registracija) i model izdvaja nove lezije;
  oba snimka se prikazuju jedan pored drugog
- pregledač: tri ravni, listanje preseka, lenjir sa položajima lezija, skok na leziju, mapa pouzdanosti
- pouzdanost svake detekcije (visoka / srednja / niska)
- strukturiran izveštaj: predlog zaključka koji lekar menja i potvrđuje, štampa / PDF
- grafik broja i zapremine lezija kroz vreme

Analiza se izvršava u pozadini. Na računaru bez grafičke kartice traje deset i više minuta po snimku.

## Testovi

    cd backend
    python -m pytest testovi -q

Testovi koriste privremenu SQLite bazu i zamenu za model, pa ne traže ni PostgreSQL ni modele.

## Čišćenje stare verzije

`ocisti_staro.bat` briše fajlove stare verzije aplikacije (stari probni snimci, stari modeli, stari izvorni fajlovi).
Pre brisanja ispisuje spisak i traži potvrdu.
