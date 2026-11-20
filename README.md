# MS sistem — automatska detekcija i praćenje lezija multiple skleroze

Veb aplikacija za automatsku segmentaciju lezija multiple skleroze na MR snimcima mozga i
kičmene moždine, sa praćenjem bolesti kroz vreme. Prateći kod uz master rad *Automatska
detekcija i praćenje lezija multiple skleroze*, Elektronski fakultet u Nišu.

Sistem koristi tri modela obučena okvirom [nnU-Net](https://github.com/MIC-DKFZ/nnUNet) v2:

| Model | Ulaz | Zadatak |
|---|---|---|
| `Dataset001_MsBrain` | 1 kanal: FLAIR | sve lezije mozga |
| `Dataset021_BrainNew` | 2 kanala: raniji + noviji FLAIR | nove lezije između dva pregleda |
| `Dataset013_SpineNOREG` | 2 kanala: T2 + STIR / PSIR / MP2RAGE | lezije kičmene moždine |

Lekar unosi pregled, sistem izvršava segmentaciju u pozadini i vraća merenja po leziji
(zapremina, položaj, pouzdanost detekcije), pregledač snimaka u tri ravni, predlog
strukturiranog radiološkog izveštaja i grafik toka bolesti kroz vreme.

Sistem je zamišljen kao alat za podršku lekaru, ne kao zamena za njegovu procenu. Konačnu
odluku i potvrdu izveštaja uvek donosi lekar.

## Tehnologije

- **Backend** — Python, FastAPI, SQLAlchemy, PostgreSQL
- **Analiza** — PyTorch, nnU-Net v2, SimpleITK (registracija), NiBabel, SciPy
- **Frontend** — React, Vite, React Router

## Struktura projekta

```
backend/
  main.py              pokretanje servera, nastavak prekinutih analiza
  konfiguracija.py     podešavanja: baza, putanje, modeli, pragovi pouzdanosti
  baza.py              šema baze podataka (SQLAlchemy)
  sigurnost.py         heširanje lozinki (scrypt) i JWT tokeni
  rute_*.py            REST API: nalog lekara, pacijenti, pregledi, preseci, izveštaj
  analiza/
    motor.py           učitavanje nnU-Net modela i segmentacija
    registracija.py    rigidna registracija i prevođenje sekvenci (SimpleITK)
    posao.py           pozadinski red analiza
    merenja.py         izdvajanje lezija, zapremine i pouzdanost
    prikaz.py          preseci i slojevi lezija kao PNG slike
    nalaz.py           predlog strukturiranog izveštaja
frontend/src/
  stranice/            prijava, radna lista, karton, pregled, izveštaj, podešavanja
  delovi/              pregledač snimaka, grafik toka bolesti, forme za unos
notebooks/             obučavanje i evaluacija modela (Google Colab)
```

## Pokretanje

### 1. Baza podataka

Potreban je PostgreSQL sa praznom bazom:

```bash
createdb ms_sistem
```

Tabele se prave same pri prvom pokretanju servera.

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Server se podiže na `http://localhost:8000`.

Podešavanja se čitaju iz okruženja ili iz fajla `backend/.env` (nije u repozitorijumu).
Sve promenljive imaju podrazumevane vrednosti, pa za lokalni rad `.env` najčešće nije
potreban. Najvažnije:

| Promenljiva | Podrazumevano | Značenje |
|---|---|---|
| `MS_BAZA_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/ms_sistem` | veza ka bazi |
| `MS_MODELI` | `backend/modeli` | folder sa nnU-Net modelima |
| `MS_PODACI` | `backend/podaci` | snimci, rezultati analiza |
| `MS_UREDJAJ` | `auto` | `auto` koristi GPU ako postoji, inače CPU |
| `MS_DOZVOLJENI_IZVORI` | `http://localhost:5173,http://127.0.0.1:5173` | adrese frontenda (CORS) |

### 3. Modeli

Modeli nisu u repozitorijumu zbog veličine. Svaki od tri modela se smešta u
`backend/modeli/` tako da zadrži strukturu koju nnU-Net pravi:

```
backend/modeli/
  Dataset001_MsBrain/
    nnUNetTrainer_100epochs__nnUNetPlans__3d_fullres/
      plans.json
      dataset.json
      fold_0/
  Dataset021_BrainNew/
    ...
  Dataset013_SpineNOREG/
    ...
```

Dovoljno je kopirati `plans.json`, `dataset.json` i ceo folder `fold_0`. Stranica
**Podešavanja** u aplikaciji pokazuje koji su modeli pronađeni i da li se analiza izvršava
na GPU ili CPU.

Bez modela aplikacija se pokreće i radi, ali analiza snimka ne može da se izvrši.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplikacija se otvara na `http://localhost:5173`. Ako backend nije na `localhost:8000`,
adresa se zadaje promenljivom `VITE_API`.

## Ulazni podaci

Snimci se učitavaju u formatu **NIfTI** (`.nii` ili `.nii.gz`), kako su objavljeni javni
skupovi korišćeni u radu. DICOM i povezivanje sa bolničkim PACS sistemom nisu podržani —
to je naveden pravac daljeg razvoja.

Za kontrolni pregled (nove lezije) pacijent mora imati **raniji pregled iste regije sa
ranijim datumom snimanja**; raniji snimak se rigidno registruje na noviji pre poređenja.

## Notebook-ovi

Obučavanje i evaluacija rađeni su u Google Colab okruženju. Svi notebook-ovi su sačuvani
sa izlazima.

| Notebook | Namena |
|---|---|
| `Master_mozak_nnUNet.ipynb` | priprema podataka i obučavanje modela svih lezija |
| `Master_mozak_EVALUACIJA_v2_SLIKE.ipynb` | evaluacija svih lezija na četiri skupa, slike preklapanja |
| `Master_mozak_NOVE_LEZIJE_v2.ipynb` | obučavanje modela novih lezija |
| `Master_mozak_NOVE_LEZIJE_EVAL.ipynb` | evaluacija novih lezija i kontrola „isti snimak dvaput" |
| `Master_kicma_nnUNet.ipynb` | model v1 za kičmenu moždinu (samo T2) |
| `Master_kicma_REG_NOREG.ipynb` | modeli NOREG i REG i poređenje tri modela |
| `Master_REGISTRACIJA.ipynb` | rigidna registracija na sirovim podacima |
| `Master_REGISTRACIJA_TIPOVI.ipynb` | poređenje tipova registracije |
| `Master_SLIKE_kicma_nove.ipynb` | slike rezultata za kičmenu moždinu i nove lezije |

## Podaci

Snimci pacijenata, obučeni modeli i rezultati analiza nisu u repozitorijumu. Korišćeni su
javno dostupni skupovi: MS3SEG, MSLesSeg, open_ms_data, MSSEG-2016, MSSEG-2 i
MS-Multi-Spine. Detalji o skupovima, podeli podataka i rezultatima nalaze se u radu.


