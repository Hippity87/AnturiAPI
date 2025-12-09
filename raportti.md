# Harjoitustyön raportti

## 1. Ohjelman asennus ja käynnistys

Ohjelma on toteutettu Python-versiolla **3.13**. Varmista, että koneeltasi löytyy tämä versio.

**Vaaditut toimenpiteet:**

1.  **Virtuaaliympäristön luonti:**
    Navigoi projektin juureen ja aja:
    `python -m venv venv`

2.  **Virtuaaliympäristön aktivointi:**
    * Windows: `.\venv\Scripts\activate`
    * Mac/Linux: `source venv/bin/activate`

3.  **Riippuvuuksien asennus:**
    `pip install -r requirements.txt`

4.  **Ohjelman käynnistys:**
    `fastapi dev app/main.py`
    *(Tai vaihtoehtoisesti: `uvicorn app.main:app --reload`)*

Kun palvelin on käynnissä, API-dokumentaatio (Swagger UI) löytyy osoitteesta:
`http://127.0.0.1:8000/docs`

---

## 2. Ratkaisun perustelut ja resurssit

### Teknologiavalinnat
FastAPI, SQLModel ja SQLite olivat kurssilla tutuksi tulleita ja tehtävänannossa määriteltyjä vaatimuksia, joten ne muodostivat työn rungon. Harkitsin aluksi PostgreSQL:n käyttöä oppimismielessä, mutta totesin SQLiten olevan tähän käyttötapaukseen erittäin toimiva ja kevyt ratkaisu, joka täyttää vaatimuksen "ei erillisiä palvelinasennuksia".

### Asynkronisuus (Async/Await)
Päätin toteuttaa sovelluksen asynkronisena, vaikka synkroninenkin toteutus (FastAPI:n säikeistyksen avulla) olisi riittänyt varsin hyvin tämän kokoluokan sovellukselle. Valintani taustalla oli halu oppia ja hyödyntää skaalautuvia "best practices" -menetelmiä heti alusta alkaen.

Vaikka asynkronisuus lisäsi monimutkaisuutta ja vei enemmän aikaa, se on modernin web-kehityksen standardi. Idea tähän syntyi lukemalla FastAPIn dokumentaatiota, ja sen vuoksi halusin suunnitella rajapinnan niin, että se on periaatteessa valmis käsittelemään suurempia kuormia tulevaisuudessa ilman, että perusarkkitehtuuria tarvitsee kirjoittaa kokonaan uudelleen.

---

## 3. Endpointien polkusuunnittelu

API:n rakenne noudattaa kerroksellista arkkitehtuuria (`routers` -> `crud` -> `models` -> `database`), jota jalostin kurssin esimerkkien ja tekoälyn avustuksella.

### Hierarkia ja resurssit
Polkusuunnittelua ohjasi selkeä "Parent-Child" -ajattelu. Esimerkiksi mittauksen luonti tapahtuu polussa `/sensors/{id}/measurements`, koska mittausdata on aina alisteista tietylle anturille. Tämä heijastaa suoraan tietokannan rakennetta, jossa mittauksella on viiteavain (`sensor_id`) anturitauluun.

### Tunnisteet ja käytettävyys (ID vs. MAC)
Vaikka vaatimusmäärittelyssä puhuttiin yleisesti "tunnisteesta", päädyin palauttamaan rajapinnasta sekä tietokannan sisäisen `id`:n että laitteen `mac_id`:n.

Tämä ratkaisu perustuu käytännönläheiseen ajatteluun tehdasympäristössä:
* **Tietokanta-ID (esim. 7):** On lyhyt ja helppo käyttää URL-osoitteissa ja nopeassa kommunikaatiossa ("Tarkista anturi 7").
* **MAC-osoite:** On laitteen fyysinen, uniikki tunniste.

Palauttamalla molemmat mahdollistetaan tilanne, jossa valvomo voi ohjeistaa huoltohenkilöä tarkistamaan "Anturin 7", ja paikan päällä huoltaja voi varmistaa MAC-osoitteen avulla, että kyseessä on varmasti oikea laite. Tämä vähentää inhimillisten virheiden riskiä.

Tässä on toki otettava huomioon, että jos joskus lisätään johonkin lohkoon lisää antureita, niiden ID voi olla vaikka 106, kun taas vieressä on anturi 7, joka asennettiin järjestelmän rakennusvaiheessa. Olen olettanut, että tämä hoidetaan dokumentaatiolla hyvin, ja vaikka jälkikäteen lisätyn anturin numerointi poikkeaa totutusta, `id`/`mac_id`-skeema toimii silti luotettavasti tunnistamisessa.

---

## 4. Mitä opin työtä tehdessä?

Tämä harjoitustyö kokosi yhteen REST API -kehityksen teorian ja käytännön. Tärkeimmät oppimistulokset olivat:

* **REST-arkkitehtuurin palaset:** Opin ymmärtämään syvällisesti, miten API rakentuu olennaisista osistaan: CRUD-mallista, endpointeista ja datan mallintamisesta. Hahmotan nyt, miten tietokantakerros, sovelluslogiikka ja ulospäin näkyvä rajapinta keskustelevat keskenään.
* **Asynkronisuus:** Ymmärsin käytännössä, miten `async/await` toimii Pythonissa ja miksi on kriittistä, ettei asynkronisen funktion sisällä kutsuta synkronisia, blokkaavia metodeja.
* **SQLModel & ORM:** Opin käyttämään SQLModelia ja ymmärsin eron Pydantic-mallien (tiedonsiirto) ja tietokantamallien (tallennus) välillä.
* **Olennaisin oppi:** Merkittävin tulos on se, että REST API ei tunnu enää vieraalta kirjainyhdistelmältä tai abstraktilta käsitteeltä. Se on muuttunut selkeäksi työkaluksi, jonka osaan nyt suunnitella ja toteuttaa itsenäisesti. Arkkitehtuurin suunnittelutaitoni ovat kehittyneet, ja käytetyt työkalut ovat tulleet tutuiksi.

---

## 5. Tekoälyn hyödyntäminen ja laadunvarmistus

Tässä työssä tekoäly (pääasiassa Google Gemini) toimi "sparrauskumppanina" ja tuottavuustyökaluna. Olen tehnyt kurssin harjoitukset itsenäisesti ilman tekoälyä, mutta tässä laajemmassa harjoitustyössä käytin sitä nopeuttamaan koodausta ja selittämään kirjastojen toiminnallisuuksia.

### Mihin ja miksi käytin tekoälyä?

1.  **Syntaksi ja kirjastot:** Taustani on vahvemmin C#-maailmassa, joten Pythonin kanssa toiminta on hitaampaa. Tässä tekoäly löysi minulle työkalut joita haluan käyttää nopeiten ja auttoi myös niiden oikeaoppisessa käytössä.
2.  **Arkkitehtuurin validointi:** Suunnittelin itse sovelluksen arkkitehtuurin, joka poikkesi opettajan esimerkeistä. Syötin suunnitelmani tekoälylle ja pyysin sitä etsimään "Clean Code" -periaatteiden vastaisia ratkaisuja tai aukkoja REST-suunnittelussa. Tämä auttoi löytämään pullonkauloja jo ennen koodaamista.
3.  **Koodin generointi luonnollisesta kielestä:** Usein hahmotin prosessin ensin sanallisesti (pseudokoodina), ja annoin tekoälyn muodostaa siitä varsinaisen Python-toteutuksen. Tämä säästi aikaa kirjoittamiselta, mutta vaati tarkkaa valvontaa, sillä virheitäkin tuli.
4.  **Tietokanta:** SQLModel- ja aiosqlite-toteutukset ovat olleet itselleni vieraampia, joten näissä nojasin vahvasti tekoälyn tuottamiin esimerkkeihin.
5.  **Viimeistely ja dokumentaatio:** Refaktoroinnin lisäksi tekoälyä hyödynnettiin yleiseen siistimiseen; esimerkiksi Swagger-dokumentaation vaatimat `summary`- ja `description`-tekstit generoitiin näppärästi tekoälyn avulla.

### Miten varmistin laadun ja oikeellisuuden?

En kopioinut koodia sokeasti. Varmistin tekoälyn tuotosten toimivuuden seuraavilla tavoilla:

* **Logiikan tarkistus:** Huomasin usein tekoälyn ehdotuksissa loogisia virheitä ("ajatusvirheitä") pelkästään lukemalla koodia, ennen kuin edes ajoin sitä (enkä siis edes ajanut). Tekoäly saattoi esimerkiksi unohtaa muutoksen vaikutukset toisaalla ohjelmassa, vaikka sille oli annettu koko projektin konteksti.
* **Manuaalinen debuggaus:** Kun virheitä ilmeni, en vain syöttänyt virheilmoitusta takaisin tekoälylle, vaan luin terminaalin stack trace -tulosteet ja selvitin virheen syyn itse dokumentaatiosta.
* **Testaus:** Testasin endpointteja aktiivisesti Swagger UI:n kautta varmistaakseni, että ne palauttavat haluttua dataa.

### Konkreettisia esimerkkejä korjauksista

Vaikka tekoäly nopeutti työtä, se teki myös virheitä, jotka minun piti korjata:

1.  **Hallusinaatiot:** Yhdessä vaiheessa Gemini alkoi yllättäen generoida Java-koodia Python-projektin keskelle ja nimesi luokkia suomeksi, vaikka projekti oli englanninkielinen. Tämä muistutti siitä, että kielimallin tuotosta pitää aina valvoa.
2.  **Async/Sync sekoittaminen:** Päätin hyödyntää `async`-toiminnallisuutta suorituskyvyn parantamiseksi. Tekoäly auttoi syntaksissa, mutta teki virheitä kutsumalla synkronisia (blokkaavia) metodeja asynkronisten funktioiden sisältä, mikä aiheutti IO-ongelmia. Nämä ratkaisin lukemalla FastAPIn dokumentaatiota ja korjaamalla `await`-kutsujen logiikan.
3.  **Transaktioiden hallinta (Case: Sensorin luonti):**
    * *Ongelma:* Kun uusi anturi luodaan, halusin siitä heti merkinnän historiaan. Tekoäly ehdotti ratkaisua, jossa anturi luodaan ja commitoidaan ensin, ja vasta sitten yritetään luoda historiatapahtuma.
    * *Ratkaisuni:* Tunnistin tässä riskin tietojen eheydelle: jos prosessi katkeaa tai epäonnistuu vaiheiden välissä (esim. anturin luonti epäonnistuu, mutta koodi yrittää silti luoda tapahtuman virheellisellä/puuttuvalla ID:llä), tietokantaan jäisi "haamuja" tai vaillinaista dataa. Korjasin logiikan käyttämään yhtä transaktiota ja session.flush()-komentoa.
    * *Lopputulos:* Flush antaa anturin ID:n käyttöön heti, mutta molemmat rivit tallentuvat kantaan vasta lopullisessa commit-vaiheessa. Tämä tekee operaatiosta ACID-periaatteiden mukaisen (kaikki tai ei mitään), mikä takaa tietoeheyden ja vähentää tarvetta ylimääräisille virhetarkistuksille koodissa.
4.  **Refaktorointi:** Pydantic-malleissa oli paljon toistoa. Pyysin tekoälyä refaktoroimaan mallit periytymistä ja muita ohjeitani hyödyntäen, minkä tuloksena koodimäärä väheni ja luettavuus parani.