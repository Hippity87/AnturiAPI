# Anturi API

REST API tehdasympäristön lämpötila-antureiden hallintaan ja datan keräämiseen.

## Teknologiat
* **Kieli:** Python 3.13
* **Framework:** FastAPI
* **Tietokanta:** SQLite (Async)
* **ORM:** SQLModel (SQLAlchemy)

## Asennus ja käynnistys

1. **Projektin alustus**
    git clone https://github.com/Hippity87/AnturiAPI.git
    cd AnturiAPI

2. **Luo virtuaaliympäristö:**
    python -m venv venv

3. **Aktivoi virtuaaliympäristö**
    win: .\venv\Scripts\activate
    linux: source venv/bin/activate

4. **Asenna riippuvuudet**
    pip install -r requirements.txt

5. **Käynnistä Palvelin**
    uvicorn app.main:app
    # TAI dev
    fastapi dev app/main.py

6. **Dokumentaatio**
    https://127.0.0.1:8000/docs

