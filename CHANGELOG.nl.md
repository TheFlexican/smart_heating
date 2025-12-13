# Wijzigingslogboek

Alle belangrijke wijzigingen aan dit project worden gedocumenteerd in dit bestand.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
en dit project volgt [Semantic Versioning](https://semver.org/).

## [Niet Uitgebracht]

### ✨ Functies
### 🐛 Opgeloste bugs & Verbeteringen

## [0.5.14] - 2025-12-13

### 🐛 Opgeloste bugs & Verbeteringen

- Backend schema's: accepteert nu numerieke dagindices (0=Maandag) of korte 3-letter codes (mon, tue, ...). Volledige dagnamen zijn niet langer toegestaan via de API. Frontend en docs bijgewerkt om indices te gebruiken.


## [0.5.13] - 2025-12-12

### 🐛 Opgeloste bugs & Verbeteringen

**Test Suite Stabiliteit**
- Asyncio task hangende problemen in test suite opgelost door correct awaiten van geannuleerde achtergrondtaken
- Uitgebreide task cleanup toegevoegd in test fixtures met `asyncio.gather(*tasks, return_exceptions=True)`
- Alle 1222 tests slagen nu consistent in ~12 seconden (voorheen oneindig hangend)
- 87.33% code coverage bereikt (overschrijdt 80% vereiste)
- Problematische debug test bestand verwijderd dat timeout problemen veroorzaakte

**Achtergrondtaak Beheer**
- Achtergrondtaak lifecycle management in coordinator, veiligheidsmonitor en zone logger gerepareerd
- Alle `asyncio.create_task()` en `hass.async_create_task()` aanroepen slaan nu correct task referenties op
- Tasks worden bijgehouden in sets en geannuleerd tijdens shutdown om resource leaks te voorkomen
- Toegevoegd `add_done_callback()` om voltooide tasks automatisch te verwijderen uit tracking sets

**Code Kwaliteit**
- Thermostaat idle hysteresis-logica: de thermostaat setpoint respecteert nu correct de hysteresis wanneer het gebied idle is
- Wanneer de gebiedstemperatuur >= (doel - hysteresis), wordt de thermostaatinstelling verlaagd naar de huidige temperatuur om te voorkomen dat de 'verwarming' status wordt geschakeld
- Voorkom dubbele calls naar `climate.set_temperature` door de laatst ingestelde setpoint per thermostaat in de cache op te slaan
- Tests en ontwikkelaarsdocumentatie bijgewerkt om problemen met MagicMock numerieke conversie te voorkomen
- Fix: De Zone-instelling "Schakel schakelaars/pompen uit wanneer niet verwarmd wordt" (Switch/Pump Control) werkte niet correct en veranderde niet persistent; de API retourneert nu `shutdown_switches_when_idle` (achterwaarts compatibel met `switch_shutdown_enabled`).
- Breaking change: De backend accepteert nu uitsluitend numerieke dagindices (0=Maandag) of korte 3-letter codes ('mon','tue',...). Voluit geschreven en gelokaliseerde dagnamen (bijv. 'Maandag', 'Monday') worden niet meer geaccepteerd via de API. De frontend is aangepast om indices te verzenden.

**OpenTherm Ketel Monitoring & Foutmeldingen**
- **Real-time ketel status dashboard**: Live OpenTherm Gateway sensor monitoring
  - Toont ketel operatie: CV Actief, Warm Water Actief, Vlam Status, Modulatie Niveau
  - Toont watertemperaturen: Controle Setpoint, CV Water, Retour Water
  - Monitort systeemdruk en kamertemperatuur/setpoint
  - Auto-refresh elke 5 seconden voor live updates
- **Kritieke foutdetectie & waarschuwingen**: Automatische monitoring van 7 ketel foutstatussen
  - Storingsindicatie - hoofdfout vlag
  - Lage waterdruk waarschuwing
  - Gasstoring detectie
  - Luchtdrukfout monitoring
  - Water overtemperatuur alarm
  - Service vereist melding
  - Diagnostische indicatie
- **Multi-kanaal notificaties**: Dubbel notificatiesysteem voor ketel problemen
  - Push notificaties naar mobiel (notify.mobile_app_iphone) met alarm geluid
  - Persistente notificaties in Home Assistant UI
  - Fout details: sensor naam, vriendelijke naam, tijdstempel
  - Gegroepeerde notificaties per fout type
- **Veiligheid integratie**: OpenTherm fout sensors kunnen toegevoegd worden aan Globale Instellingen → Veiligheid
  **OpenTherm Gateway Selectie**
  - Frontend: De OpenTherm tab in Globale Instellingen toont nu een dropdown met geconfigureerde OpenTherm Gateway integratie entries (op basis van `id`/slug). Kies hier de gateway die gebruikt wordt voor globale ketelbesturing om te voorkomen dat er climate entiteit IDs worden ingevoerd.

  - Automatische verwarming shutdown wanneer ketel fouten rapporteert
  - Voorkomt schade door voortgezet gebruik tijdens storingen
  - Voorbeeld: Voeg `binary_sensor.opentherm_ketel_storingsindicatie` toe aan veiligheid sensors

**Verwarmingstype Configuratie UI**
- **Zone Instellingen UI toegevoegd voor verwarmingstype selectie**
  - Kies tussen Radiator of Vloerverwarming per zone
  - Weergegeven in Zone Details → Instellingen → "Verwarmingstype" kaart
  - Toont huidig type in badge (Radiator/Vloerverwarming)
  - Info waarschuwing legt impact op ketel setpoint uit
- **Visuele feedback**: Radioknop selectie met beschrijvingen
  - Radiator: Snelle reactie, hogere overhead temperatuur (+20°C standaard)
  - Vloerverwarming: Langzame reactie, lagere overhead temperatuur (+5°C standaard)
- **TypeScript integratie**: `heating_type` toegevoegd aan Zone interface
  - Type-veilige selectie: 'radiator' | 'floor_heating'
  - Frontend API: `setHeatingType(areaId, heatingType, customOverheadTemp?)`

**Veiligheidssensor Beheer Fixes**
- **Veiligheidssensor toevoegen/verwijderen API gefixed**: Backend handlers gecorrigeerd
  - `handle_set_safety_sensor`: Gebruikt nu `add_safety_sensor()` i.p.v. niet-bestaande `clear_safety_sensors()`
  - `handle_remove_safety_sensor`: Accepteert sensor_id parameter, gebruikt `remove_safety_sensor()`
  - Juiste parameter afhandeling: sensor_id, attribute, alert_value, enabled
- **Multi-sensor ondersteuning**: GET API retourneert alle veiligheid sensors
  - Retourneert `{sensors: [...], alert_active: bool}` i.p.v. enkele sensor
  - Ondersteunt meerdere veiligheid sensors tegelijk (rookmelders + OpenTherm fouten)
  - Frontend SafetySensorResponse type al compatibel

**Configureerbare Verwarmingstypes voor OpenTherm Optimalisatie**
- **Per-zone verwarmingstype configuratie toegevoegd**: Optimaliseer ketel setpoint voor verschillende verwarmingssystemen
  - Ondersteuning voor radiatoren (standaard) en vloerverwarming types
  - Aangepaste overhead temperatuur overschrijving (0-30°C)
  - Slimme setpoint berekening: vloerverwarming +10°C, radiatoren +20°C
  - Gemengd systeem ondersteuning: gebruikt hoogste overhead voor veiligheid
- **Verbeterde OpenTherm logging**: Toont verwarmingstype uitsplitsing in logs
  - Toont aantal vloerverwarming vs radiator zones actief
  - Toont overhead temperatuur gebruikt voor setpoint berekening
  - Voorbeeld: "Boiler ON - Setpoint: 35.0°C | overhead +10°C | 1 floor heating + 0 radiator"
- **Nieuw API endpoint**: `POST /api/smart_heating/areas/{area_id}/heating_type`
  - Stel verwarmingstype in: "radiator" of "floor_heating"
  - Configureer aangepaste overhead temperatuur
  - Invoer validatie voor verwarmingstype en overhead bereik
- **Efficiëntie verbeteringen voor vloerverwarming**:
  - Lagere watertemperaturen (30-40°C in plaats van 50-60°C)
  - Betere modulatie efficiëntie (20-30% in plaats van 40-50%)
  - Verminderd schakelen, langere brandtijden, lager energieverbruik
  - Comfortabelere en stabielere vloerverwarming werking

  **Verbeterde standaard verwarmingscurve en minimum setpoint voor snellere opwarming**
  - Bijgewerkte standaard verwarmingscurve basis-offsets en minimum setpoints voor realistischere systeemrespons:
    - Vloerverwarming: basis aanvoertemperatuur is 40°C (was 20°C)
    - Radiatoren: basis aanvoertemperatuur is 55°C (was 27.2°C)
    - De minimale setpoint die wordt afgedwongen door de controller is nu type-gebonden: vloer=40°C, radiatoren=55°C
    Deze waarden verminderen doorgaans de tijd die nodig is om de target temperatuur te bereiken. Pas de `heating_curve_coefficient` per zone aan indien meer fijngevoeligheid gewenst is.

**Mushroom-Stijl UI Verbeteringen**
- **Mushroom-geïnspireerd kaart ontwerp geïmplementeerd**: Moderne, gepolijste interface met vloeiende transities
  - Afgeronde hoeken (borderRadius: 3) voor alle kaarten en componenten
  - Alpha-gemengde achtergronden voor visuele diepte
  - Verhoogde schaduwen met vloeiende transities bij hover/interactie
  - Verbeterde visuele hiërarchie met Material Design principes
- **Slepen-en-neerzetten toegevoegd voor zone kaarten**: Herorganiseer zones op hoofddashboard
  - Sleep handgreep met grip icoon in linkerbovenhoek van elke zone kaart
  - Visuele feedback tijdens slepen (opacity wijziging, elevatie)
  - Volgorde blijft behouden in localStorage tussen pagina verversingen
  - Vloeiende animaties voor herschikking
- **Verbeterde vertalingen**: Volledige vertaalondersteuning voor alle UI elementen
  - Apparaat statussen: heating/verwarmen, idle/inactief, off/uit, cooling/koelen
  - Zone badges: HEATING/VERWARMEN, IDLE/INACTIEF, OFF/UIT
  - Aanwezigheid statussen: HOME/THUIS, AWAY/WEG
  - HVAC acties correct vertaald in apparaat chips
  - Alle vertalingen bevatten fallback waarden voor robuustheid
- **App-eigen thema schakelaar**: Eenvoudige licht/donker modus bediening zonder HA afhankelijkheden
  - Thema schakelaar in Globale Instellingen → Geavanceerd tab
  - Voorkeur blijft behouden in localStorage ('appThemeMode')
  - Geen complexe parent window detectie of cross-origin problemen
  - Schone, betrouwbare thema schakel ervaring

**Beschikbare Apparaten Paneel Verbeteringen**
- **Scroll probleem in Beschikbare Apparaten sidebar opgelost**: Juiste hoogte beperking toegevoegd om scrollen mogelijk te maken
  - Paneel scrollt nu correct wanneer de apparatenlijst lang is
  - Overflow gedrag gefixed voor betere UX op hoofddashboard
- **Verberg optie toegevoegd voor Beschikbare Apparaten paneel**: Nieuwe UI instelling om sidebar te verbergen wanneer setup compleet is
  - Toggle schakelaar in Globale Instellingen → Geavanceerd → Gebruikersinterface sectie
  - Instelling: "Verberg Beschikbare Apparaten Paneel"
  - Handig na initiële setup om schermruimte te maximaliseren voor zone monitoring
  - Instelling is persistent en opgeslagen in storage
  - Pagina herlaadt automatisch bij wisselen om wijzigingen toe te passen

**Snelle Boost Toegang op Zone Kaarten**
- **Boost knop toegevoegd aan zone kaarten**: Snelle één-klik boost activering vanaf hoofddashboard
  - Raket icoon knop (🚀) verschijnt naast menu knop op elke zone kaart
  - Visuele feedback: Grijs wanneer inactief, rode achtergrond wanneer boost actief is
  - "BOOST" status chip toont in kaart header wanneer boost modus actief is
  - Één-klik activering met opgeslagen boost instellingen van de zone (temperatuur & duur)
  - Klik opnieuw om boost modus te annuleren
  - Gedetailleerde boost configuratie (temp/duur) blijft in zone detail instellingen
  - Verbetert UX door aantal klikken te verminderen voor snelle verwarming activering

### 🐛 Bugfixes

**Efficiëntie Rapporten UI Fixes**
- **Efficiëntie rapporten undefined fout opgelost**: API response structuur gecorrigeerd om frontend verwachtingen te matchen
  - API retourneert nu metrics gewikkeld in `metrics` object volgens TypeScript interface
  - Opgelost: `TypeError: undefined is not an object (evaluating 'E.metrics.energy_score')`
  - Beide endpoints bijgewerkt: `/api/smart_heating/efficiency/all_areas` en `/efficiency/report/{area_id}`
  - Response bevat nu correcte structuur: `{area_id, period, metrics: {energy_score, ...}, recommendations}`
- **Terug knoppen toegevoegd aan alle pagina componenten**: Verbeterde navigatie UX
  - Terug knop (←) toegevoegd aan Efficiëntie Rapporten pagina
  - Terug knop (←) toegevoegd aan Historische Vergelijkingen pagina
  - Terug knop (←) toegevoegd aan Gebruikersbeheer pagina
  - Terug knop (←) toegevoegd aan Vakantiemodus Instellingen pagina
  - Terug knop (←) toegevoegd aan Importeren/Exporteren pagina
  - Alle terug knoppen navigeren naar hoofdscherm (`/`)

**Nacht Boost Kritieke Fix**
- **Nacht boost werkt nu correct**: Nacht boost activeert nu correct tijdens actieve schema's
  - Vorig gedrag: Nacht boost werd geblokkeerd wanneer ER EEN schema actief was
  - Nieuw gedrag: Nacht boost werkt additief bovenop actieve schema's (bijv. slaap preset)
  - Voorbeeld: Slaap preset (18.5°C) + Nacht boost (0.2°C) = 18.7°C tijdens nachturen
  - Dit maakt geleidelijk voorverwarmen mogelijk voordat het ochtendschema start
- **Verbeterde smart night boost logging**: Betere foutmeldingen wanneer voorspelling faalt
  - Legt uit wanneer temperatuursensoren nog bezig zijn met initialiseren
  - Verduidelijkt wanneer leergegevens nog niet beschikbaar zijn (heeft meerdere verwarmingscycli nodig)
  - Toont huidige en doeltemperaturen voor debugging
- **Verhoogde night boost zichtbaarheid**: Logging niveau veranderd van DEBUG naar INFO wanneer actief
  - Maakt het makkelijker om te verifiëren dat night boost werkt in productie logs
  - Logt wanneer night boost inactief is (DEBUG niveau) om ruis te verminderen

### ✨ Functies

**Geschiedenisgegevens Beheer Verbetering**
- **Verlengde bewaarperiode**: Geschiedenis bewaartermijn configureerbaar tot 365 dagen (voorheen max 30 dagen)
- **Optionele database opslag**: Voor power users met MariaDB/PostgreSQL/MySQL
  - Automatische database ondersteuning detectie (valt terug naar JSON voor SQLite)
  - Niet-blokkerende database operaties via Home Assistant's recorder
  - Behoudt in-memory cache voor snelle toegang (1000 entries per zone)
  - Achterwaarts compatibel - JSON opslag blijft de standaard
  - Automatische tabel aanmaak met geoptimaliseerd schema (geïndexeerde kolommen voor prestaties)
- **Database migratie**: Naadloze migratie tussen JSON en database opslag
  - Bidirectionele migratie (JSON ↔ Database)
  - Behoudt alle historische data tijdens migratie
  - API endpoint: POST /api/smart_heating/history/storage/migrate
  - Automatische validatie voor migratie (controleert database beschikbaarheid)
  - Data blijft behouden na Home Assistant herstarts
- **Database onderhoud API**: Vier nieuwe endpoints voor database operaties
  - GET /api/smart_heating/history/storage/info - Huidige backend en statistieken
  - GET /api/smart_heating/history/storage/database/stats - Gedetailleerde database metrieken
  - POST /api/smart_heating/history/storage/migrate - Migreer tussen backends
  - POST /api/smart_heating/history/cleanup - Handmatige opschoning trigger
- **Opslag backend configuratie**: Configureerbaar via geschiedenis config API
  - Schema validatie voor zowel bewaartermijn (1-365 dagen) als opslag backend (json/database)
  - Automatische terugval naar JSON als database niet ondersteund wordt
  - Backend voorkeur opgeslagen en hersteld na herstarts

### 🐛 Bugfixes

**Database Opslag Initialisatie Fix**
- Database validatie timing probleem opgelost waarbij validatie liep voordat recorder volledig was geïnitialiseerd
- Database validatie verplaatst van `__init__()` naar `async_load()` om te zorgen dat recorder beschikbaar is
- Backend voorkeur wordt nu geladen uit opslag voor de validatie check
- Database ondersteuning wordt correct gedetecteerd bij opstarten voor MariaDB/MySQL/PostgreSQL
- Deadlock-veroorzakende `async_block_till_done()` aanroep verwijderd tijdens validatie

**Database Migratie Fix**
- Migratie API aangepast om bron en doel backends correct bij te houden
- Migratie rapporteert nu correct de bron backend (toonde voorheen twee keer het doel)
- `_db_validated` vlag toegevoegd om dubbele validatie tijdens migratie te voorkomen
- Migratie workflow werkt nu betrouwbaar: JSON ↔ Database ↔ JSON

**SQLAlchemy 2.0 Compatibiliteit Fix**
- Database query syntax bijgewerkt voor SQLAlchemy 2.0 compatibiliteit
- Verouderde `select([columns])` syntax vervangen door `select(columns)`
- Count queries aangepast om `func.count()` te gebruiken in plaats van `.count()` methode
- Ontbrekende `func` import van sqlalchemy toegevoegd

**Efficiëntie Calculator Databron Fix**
- EfficiencyCalculator gebruikt nu HistoryTracker data in plaats van HA recorder
- Incorrecte entiteitnaam referenties verwijderd (`climate.smart_heating_{area_id}`) die niet bestaan
- Leest nu correct van 5-minuten interval geschiedenis snapshots verzameld door HistoryTracker
- Cyclus berekening bijgewerkt om correcte datapunt frequentie te gebruiken (12/uur vs 120/uur)
- Efficiëntie rapporten werken nu correct met werkelijke historische data

**WebSocket Coordinator Selectie Fix**
- WebSocket fout opgelost bij abonneren op updates (`'UserManager' object has no attribute 'async_add_listener'`)
- Nieuwe V0.6.0 services toegevoegd aan WebSocket uitsluitingslijst: `user_manager`, `efficiency_calculator`, `comparison_engine`, `config_manager`
- WebSocket identificeert nu correct de coordinator instantie in plaats van service managers te selecteren

### ✨ Functies

**Multi-Gebruiker Aanwezigheidsdetectie (v0.6.0)**
- **Individuele gebruikersvoorkeuren voor temperatuur**: Maak gebruikersprofielen met aangepaste temperatuurinstellingen voor alle presets
  - Koppel gebruikersprofielen aan Home Assistant persoon entiteiten voor automatische aanwezigheidsdetectie
  - Prioriteitssysteem (1-10) of gemiddelde strategie voor het combineren van voorkeuren wanneer meerdere gebruikers thuis zijn
  - Gebruikerstoewijzing per ruimte - pas gebruikersvoorkeuren alleen toe op specifieke zones
  - Real-time aanwezigheidsstatus tracking met visuele indicatoren
- **Gebruikersbeheer UI**: Complete interface voor het beheren van gebruikersprofielen
  - Aanmaken, bewerken en verwijderen van gebruikersprofielen
  - Configureer 6 preset temperaturen per gebruiker (thuis, weg, slapen, eco, comfort, boost)
  - Stel prioriteitsniveaus in en selecteer voorkeurcombinatiestrategie
  - Bekijk actieve gebruikers en hun aanwezigheidsstatus
  - Toegang via Instellingen → Gebruikersbeheer
- **API endpoints**: Volledige REST API voor gebruikers CRUD operaties en voorkeurqueries
  - GET/POST /api/smart_heating/users - Lijst en maak gebruikers aan
  - GET/PUT/DELETE /api/smart_heating/users/{user_id} - Beheer individuele gebruikers
  - GET /api/smart_heating/users/active_preferences - Haal gecombineerde voorkeuren op voor actieve gebruikers

**Verwarmingsefficiëntie Rapporten (v0.6.0)**
- **Prestatie-analyse**: Uitgebreide efficiëntie metrieken voor alle verwarmingszones
  - Energie score (0-100) gebaseerd op verwarmingscycli, temperatuurstabiliteit en tijdsefficiëntie
  - Verwarmingstijd percentage - volg hoe lang verwarming actief is
  - Verwarmingscyclus telling - identificeer zones met overmatig schakelen
  - Gemiddeld temperatuurverschil - meet hoe ver zones van doeltemperaturen afwijken
  - Automatische aanbevelingen gebaseerd op prestatie-analyse
- **Tijdsperiode analyse**: Bekijk efficiëntie over verschillende tijdspannes
  - Dag, week, maand en jaar weergaven
  - Historische trend tracking
  - Zone-per-zone vergelijkingstabellen
- **Analytics UI**: Interactief dashboard met grafieken en metrieken
  - Overzichtsweergave met alle zones gerangschikt op efficiëntie
  - Gedetailleerde per-zone uitsplitsingen met specifieke aanbevelingen
  - Kleurgecodeerde scores (Uitstekend/Goed/Redelijk/Slecht)
  - Toegang via Analytics → Efficiëntie Rapporten
- **API endpoints**: Efficiëntiedata ophalen voor alle zones
  - GET /api/smart_heating/efficiency/report/{area_id} - Enkele zone efficiëntie
  - GET /api/smart_heating/efficiency/all_areas - Vergelijk alle zones

**Historische Vergelijkingen (v0.6.0)**
- **Periode-over-periode analyse**: Vergelijk verwarmingsprestaties over tijd
  - Vergelijk huidige dag/week/maand/jaar met vorige periode
  - Aangepaste datumbereik vergelijkingen voor twee willekeurige perioden
  - Delta berekeningen die verbeteringen of verslechteringen tonen
  - Percentage verandering indicatoren met trend pijlen
- **Multi-metriek vergelijking**: Volg veranderingen over alle efficiëntie metrieken
  - Energie score delta's
  - Verwarmingstijd veranderingen
  - Cyclus telling variaties
  - Temperatuurverschil trends
- **Vergelijking UI**: Visuele interface voor het analyseren van prestatieveranderingen
  - Zij-aan-zij metriek vergelijkingen
  - Verbetering/verslechtering indicatoren met kleurcodering
  - Samenvattingstekst die algemene trends uitlegt
  - Zone sortering op verbeteringsniveau
  - Toegang via Analytics → Historische Vergelijkingen
- **API endpoints**: Vergelijkingsdata voor vooraf ingestelde en aangepaste perioden
  - GET /api/smart_heating/comparison/{period} - Vooraf ingestelde periode vergelijking
  - POST /api/smart_heating/comparison/custom - Aangepast datumbereik vergelijking

**Primaire Temperatuursensor Selectie**
- **Selecteer welk apparaat de temperatuur meet**: Kies een specifieke temperatuursensor of thermostaat voor elke ruimte
  - Handig wanneer je meerdere temperatuur bronnen hebt (bijv. airconditioning + aparte temperatuursensor)
  - Geef voorkeur aan een losse temperatuursensor boven de ingebouwde sensor van een AC voor nauwkeurigere metingen
  - Automatische modus (standaard): Middelt alle temperatuursensoren en thermostaten in de ruimte
  - Primaire modus: Gebruikt alleen het geselecteerde apparaat voor temperatuurmeting
  - Automatische fallback: Als primaire sensor niet beschikbaar is, keert tijdelijk terug naar automatische modus
- **UI verbeteringen**:
  - Nieuwe dropdown selector in Ruimte Detail → Apparaten tab
  - Toont alle beschikbare temperatuursensoren en thermostaten
  - Real-time temperatuur updates bij selectie wijziging
  - Beschikbaar in zowel Engels als Nederlands
- **API endpoint**: `POST /api/smart_heating/areas/{area_id}/primary_temp_sensor`

### 📱 Mobiele Verbeteringen

**WebSocket Mobiele Herverbinding (v0.5.8)**
- **Verbeterde ondersteuning voor mobiele browsers**: Verbeterde WebSocket betrouwbaarheid op iOS en Android
  - Maximale herverbindingspogingen verhoogd van 5 naar 10 voor mobiele scenario's
  - `visibilitychange` event handler toegevoegd om te herverbinden wanneer app zichtbaar wordt
  - `focus` event handler toegevoegd voor iOS Safari-specifieke herverbinding
  - Keepalive ping geïmplementeerd elke 30 seconden om time-out te voorkomen
  - Herverbindingspogingen gereset wanneer pagina zichtbaar wordt voor sneller herstel
- **Betere verbindingsbeheer**:
  - Voorkomt dubbele verbindingen wanneer al verbonden/bezig met verbinden
  - Intentionele close vlag voorkomt ongewenste herverbindingen
  - Uitgebreide console logging met `[WebSocket]` prefix voor debugging
- **Mobiele browser gedrag**:
  - Mobiele browsers sluiten vaak WebSocket verbindingen wanneer app naar achtergrond gaat
  - Automatisch herverbinden wanneer gebruiker terugkeert naar app
  - Behandelt iOS Safari's agressieve verbindingsbeheer

### ⚡ Prestaties

**Apparaat Discovery Optimalisatie (v0.5.8)**
- **Apparaat discovery caching geïmplementeerd**: Redundante discovery op elke API aanroep geëlimineerd
  - Apparaat lijst nu gecached na initiële discovery
  - Cache blijft behouden over API aanroepen naar `/api/smart_heating/devices`
  - Gebruik `/api/smart_heating/devices/refresh` om opnieuw te discoveren
  - Vermindert Home Assistant entity registry queries van ~elke 30 seconden naar alleen on-demand
- **Prestatie impact**:
  - Elimineert onnodige CPU gebruik door herhaalde entity registry scans
  - Snellere API response tijden (gecachte lijst direct geretourneerd)
  - Discovery gebeurt alleen bij opstarten en handmatige refresh
- **Gebruikerscontrole**: Gebruikers kunnen apparaat lijst verversen via zones overzicht wanneer nodig

### 🐛 Opgelost

**Kritieke Schakelaar Controle Bug Fix (v0.4.3)**
- **Onvolledige schakelaar controle logica opgelost**: Schakelaars blijven nu expliciet AAN wanneer thermostaten actief verwarmen
  - Vorige code logde alleen de intentie om schakelaars aan te houden maar voerde de actie niet uit
  - Expliciete `SERVICE_TURN_ON` aanroep toegevoegd wanneer `hvac_action == "heating"` gedetecteerd
  - Voorkomt dat warmtepompen/circulatiepompen voortijdig uitschakelen
  - Kritiek voor systemen met decimale temperatuur precisie (bijv. Google Nest thermostaten)
  - Voorbeeld: Thermostaat verwarmt naar 19.2°C terwijl zone doel 19.2°C is → schakelaar blijft nu correct AAN
- **Hoofdoorzaak**: Controle flow stond toe dat schakelaar uitschakelt ondanks dat thermostaten nog verwarmen
  - Oude flow: Log bericht → doorvallen naar `elif shutdown_switches_when_idle` → schakelaar UIT
  - Nieuwe flow: Log bericht → expliciete `SERVICE_TURN_ON` → voorkom doorvallen

### 🔧 Codekwaliteit

**Frontend Code Kwaliteit Verbeteringen (v0.4.3)**
- **App.tsx** - 5/5 SonarQube problemen opgelost:
  - Material-UI imports geconsolideerd
  - State variabele hernoemd `zones` → `areas` voor consistentie
  - `ZonesOverview` component geëxtraheerd om cognitieve complexiteit te verminderen
  - `.flatMap()` vervangen door expliciete `for...of` loops voor betere leesbaarheid
  - Alle problemen opgelost (100%)

- **ZoneCard.tsx** - 3/3 SonarQube problemen opgelost:
  - Cognitieve complexiteit verminderd door helper functies te extraheren:
    - `formatTemperature()` - Temperatuur formattering met null veiligheid
    - `isValidState()` - Status validatie
    - `getThermostatStatus()` - Thermostaat-specifieke status logica
    - `getTemperatureSensorStatus()` - Temperatuur sensor status logica
    - `getValveStatus()` - Klep status logica
    - `getGenericDeviceStatus()` - Generieke apparaat status logica
  - Verouderde `secondaryTypographyProps` vervangen door `slotProps.secondary`
  - Alle problemen opgelost (100%)

- **AreaDetail.tsx** - 32/42 SonarQube problemen opgelost (76% oplossing):
  - Alle component props `Readonly<>` gemaakt voor onveranderlijkheid
  - Verouderde `inputProps` / `InputLabelProps` vervangen door `slotProps`
  - Null-veilige optional chaining toegevoegd (`area?.target_temperature`)
  - Geneste ternaries vervangen door IIFE voor complexe conditionele rendering
  - Conflicterende `setHistoryRetention` variabelen hernoemd voor duidelijkheid
  - `String.replaceAll()` gebruikt voor schonere string vervangingen
  - `paragraph` prop vervangen door `sx={{ mb: 1 }}` voor consistentie
  - `Number.parseFloat()` / `Number.parseInt()` gebruikt i.p.v. globale functies
  - Resterende 10 problemen: Geavanceerde patronen die bredere refactoring vereisen

- **TypeScript Library Upgrade**:
  - Geüpgraded van ES2020 naar ES2021 in `tsconfig.json`
  - Maakt native `String.replaceAll()` ondersteuning mogelijk
  - Verwijdert noodzaak voor regex-gebaseerde string vervanging workarounds

### ✨ Toegevoegd

**Automatische Preset Modus Wisseling (v0.4.2)**
- **Auto Preset Modus**: Automatisch wisselen tussen preset modi op basis van aanwezigheidsdetectie
  - In-/uitschakelen per zone in Instellingen tab
  - Configureer welke preset te gebruiken bij thuis (Thuis/Comfort/Activiteit)
  - Configureer welke preset te gebruiken bij weg (Weg/Eco)
  - Werkt met zowel zone-specifieke als globale aanwezigheidssensoren
- **Slimme Woning Automatisering**: Systeem reageert op uw aanwezigheid
  - Verlaagt automatisch temperatuur naar weg preset wanneer u vertrekt
  - Herstelt automatisch thuis preset wanneer u terugkeert
  - Integreert naadloos met bestaand preset modus systeem
- **Volledige Logging**: Alle automatische preset wijzigingen gelogd in zone logs
  - Volg wanneer en waarom preset modus veranderde
  - Inclusief aanwezigheidsstatus in log entries
  - Helpt bij troubleshooting van automatiseringsgedrag

### 🔧 Codekwaliteit

**SonarQube Analyse & Code Opschoning (v0.4.1)**
- **Opgeloste Kritieke Problemen**:
  - Onbereikbare code verwijderd in `area_manager.py`
  - Ongebruikte variabelen verwijderd in hele codebase
  - Blanco `except` clausule opgelost (vangt nu specifieke `Exception`)
  - Dubbele conditionele branches verwijderd
  - Python 3.9 compatibiliteit hersteld (Optional type hints)
- **Code Organisatie**:
  - Constanten geëxtraheerd voor dubbele string literals
  - `ERROR_UNKNOWN_ENDPOINT`, `ERROR_HISTORY_NOT_AVAILABLE`, `ERROR_VACATION_NOT_INITIALIZED` toegevoegd in `api.py`
  - `ERROR_AREA_NOT_FOUND` toegevoegd in service handlers
  - `ENDPOINT_PREFIX_AREAS` constante voor consistente endpoint afhandeling
- **Verminderde Cognitieve Complexiteit**:
  - `validate_schedule_data()` gerefactored met hulpmethoden `_validate_time_format()` en `_validate_days_list()`
  - Device detectie helpers geëxtraheerd in `api.py`: `_determine_mqtt_device_type()` en `_get_ha_area_name()`
  - Verbeterde code leesbaarheid zonder functionaliteit op te offeren
- **Onderhoudbaarheid**: Alle oplosbare SonarQube problemen verholpen, resterende waarschuwingen zijn ontwerpkeuzes of false positives

### ✨ Toegevoegd

**Verbeterde Schema UI met Datumkiezers & Meerdaagse Selectie (v0.4.0)**
- **Moderne Datum/Tijd Kiezers**: Foutgevoelige tijdinvoer vervangen door Material-UI DatePicker
  - Kalender-gebaseerde datumselectie zoals vakantiemodus
  - Visuele datumselectie voor datumspecifieke schema's
  - Verbeterde gebruikerservaring met gevalideerde tijdinvoer
- **Meerdaagse Selectie**: Maak schema's voor meerdere dagen tegelijk
  - Snelkeuze knoppen: Weekdagen, Weekend, Alle Dagen
  - Checkbox interface voor individuele dagselectie
  - Preview van geselecteerde dagen voor opslaan
  - Vermindert repetitief schema aanmaken
- **Kaart-Gebaseerde Lay-out**: Moderne, inklapbare schema organisatie
  - Wekelijks terugkerende schema's gegroepeerd per dag
  - Datumspecifieke schema's in aparte sectie
  - Uitklapbare/inklapbare kaarten voor beter overzicht
  - Visueel onderscheid tussen terugkerende en eenmalige schema's
- **Datumspecifieke Schema's**: Eenmalige schema's voor specifieke datums
  - Perfect voor feestdagen, speciale evenementen of tijdelijke wijzigingen
  - Aparte sectie met kalender icoon
  - Geformatteerde datums voor gemakkelijke leesbaarheid
  - Geen impact op terugkerende wekelijkse schema's
- **Backend Verbeteringen**: Volledige ondersteuning voor nieuwe schematypen
  - `days[]` array voor meerdaagse terugkerende schema's
  - `date` veld (JJJJ-MM-DD) voor datumspecifieke schema's
  - Achterwaarts compatibel met bestaande enkel-dag schema's
  - Slimme dag formaat conversie (Maandag/mon)
- **Vertaling Ondersteuning**: Volledige Engelse en Nederlandse vertalingen
  - Alle nieuwe UI elementen vertaald
  - Schematype selectie labels
  - Meerdaagse selectie knoppen
  - Datumspecifieke schema sectie headers

**Veiligheidssensor (Rook/CO Detector) - Nooduitschakeling (v0.3.19)**
- **Veiligheidsmonitoring**: Automatische nood verwarmingsuitschakeling bij rook/CO detectie
  - Configureer elke Home Assistant binary sensor (rook, koolmonoxide, gas)
  - Real-time monitoring van sensor status wijzigingen
  - Onmiddellijke uitschakeling van ALLE verwarmingszones wanneer gevaar gedetecteerd wordt
  - Voorkomt verwarming tijdens brand of koolmonoxide noodsituaties
  - Standaard ingeschakeld wanneer sensor geconfigureerd is
  - Visuele waarschuwingen in UI wanneer veiligheidswaarschuwing actief is

**Backend Implementatie**
- Nieuwe `SafetyMonitor` module voor real-time sensor monitoring
- Area manager slaat veiligheidssensor configuratie en waarschuwingsstatus op
- Nooduitschakeling schakelt alle zones onmiddellijk uit
- Configuratie blijft behouden - zones blijven uitgeschakeld na HA herstarts
- Services: `set_safety_sensor`, `remove_safety_sensor`
- API endpoints: GET/POST/DELETE `/api/smart_heating/safety_sensor`
- WebSocket events voor veiligheidswaarschuwing notificaties
- Uitgebreide logging van veiligheidsgebeurtenissen

**Frontend Implementatie**
- Nieuwe **Veiligheid Tab** in Globale Instellingen met Beveiligings icoon (🔒)
- Configureer rook/CO detector met eenvoudige sensor picker
- Visuele status weergave:
  - Groene succes waarschuwing wanneer sensor geconfigureerd is en monitort
  - Rode fout banner wanneer veiligheidswaarschuwing actief is
  - Waarschuwing wanneer geen sensor geconfigureerd is
- Toont huidige sensor details (entiteit ID, attribuut, status)
- Eén-klik toevoegen/verwijderen veiligheidssensor
- Real-time updates wanneer sensor status wijzigt

**Test Omgeving**
- MOES rookmelder toegevoegd (`binary_sensor.smoke_detector`)
- TuYa CO detector toegevoegd (`binary_sensor.co_detector`)
- Test sensoren opgenomen in `setup.sh` voor ontwikkeling

**Vertaling Ondersteuning**
- Volledige Engelse en Nederlandse vertalingen voor veiligheidsfunctie
- UI tekst: `globalSettings.safety.*` vertaalsleutels
- Help tekst die nooduitschakeling gedrag uitlegt
- Waarschuwingsberichten voor actieve veiligheidswaarschuwingen

**Gebied-Specifieke Hysterese Override (v0.5.13)**
- **Hysterese Aanpassing**: Gebieden kunnen nu de globale hysterese instelling overschrijven
  - Schakel tussen globale hysterese (standaard 0.5°C) of gebied-specifieke waarde
  - Bereik: 0.1°C tot 2.0°C met 0.1°C stappen
  - Bijzonder nuttig voor vloerverwarming systemen (kan 0.1-0.3°C gebruiken)
  - Help modal met gedetailleerde uitleg over hysterese en verwarmingssysteem types
  - Optimistische UI updates voor directe feedback
  - Status blijft behouden bij pagina verversing

**Globale Instellingen Herontwerp (v0.5.13)**
- **Tabblad Navigatie**: Gereorganiseerde Globale Instellingen pagina met 4 tabbladen
  - 🌡️ **Temperatuur Tabblad**: Globale voorinstellingstemperaturen (6 presets)
  - 👥 **Sensoren Tabblad**: Globale aanwezigheidssensor configuratie
  - 🏖️ **Vakantie Tabblad**: Vakantiemodus instellingen (verplaatst van boven)
  - ⚙️ **Geavanceerd Tabblad**: Hysterese en toekomstige geavanceerde instellingen
  - Material-UI tabbladen met iconen voor betere visuele navigatie
  - Betere organisatie en schaalbaarheid voor toekomstige functies
  - Mobiel-vriendelijk responsief ontwerp met minder scrollen

**Backend Implementatie**
- Toegevoegd `hysteresis_override` veld aan Area model (None = gebruik globaal, float = aangepast)
- Climate controller gebruikt gebied-specifieke hysterese wanneer ingesteld
- API endpoint: `POST /api/smart_heating/areas/{area_id}/hysteresis`
- WebSocket broadcast hysterese wijzigingen in real-time
- Coordinator bevat hysteresis_override in gebied data export
- Area logger logt wanneer verwarming geblokkeerd is door hysterese

**Frontend Implementatie**
- Nieuwe **HysteresisSettings** component in Gebied Instellingen
  - Toggle schakelaar: "Gebruik globale hysterese" vs "Aangepaste hysterese"
  - Slider met visuele markers (0.1°C, 0.5°C, 1.0°C, 2.0°C)
  - Help icoon opent **HysteresisHelpModal** met gedetailleerde uitleg
  - Real-time status weergave: "Gebruikt globaal: X°C" of "Aangepast: X°C"
- Bijgewerkte **GlobalSettings** met tabblad layout
  - TabPanel component voor inhoudsorganisatie
  - Toegankelijk met ARIA labels en toetsenbord navigatie
  - Volledige EN/NL vertaling ondersteuning voor alle tabbladen
- **HysteresisHelpModal** component legt uit:
  - Wat hysterese is en waarom het belangrijk is
  - Hoe verschillende verwarmingssystemen (radiator vs vloer) verschillende waarden nodig hebben
  - Apparatuur bescherming (voorkomt kortcyclus schade)
  - Aanbevelingen gebaseerd op verwarmingssysteem type

### 📚 Documentatie
- Aangemaakt `docs/GLOBAL_SETTINGS_REDESIGN.md` - Architectuur beslissing document
  - Legt Home Assistant best practices uit: Config Flow vs Custom UI
  - Documenteert tabblad UI ontwerp en toekomstige verbetering plannen
  - Vertaling ondersteuning details
- Bijgewerkte vertaalbestanden (EN/NL) met nieuwe sleutels:
  - `globalSettings.tabs.*` - Tabblad labels
  - `globalSettings.presets.*` - Preset tabblad inhoud
  - `globalSettings.sensors.*` - Sensoren tabblad inhoud
  - `globalSettings.hysteresis.*` - Geavanceerd tabblad inhoud
  - `hysteresisHelp.*` - Help modal inhoud

### 🐛 Opgelost
- **WebSocket Fout**: Opgelost vacation_manager AttributeError in WebSocket coordinator lookup
  - Toegevoegd "vacation_manager" aan uitsluitingslijst in `websocket.py`
  - Voorkomt behandeling van VacationManager als coordinator
- **Console Opschoning**: Verwijderd alle debug console.log statements uit productie
  - Opgeschoond App.tsx, AreaDetail.tsx, useWebSocket.ts
  - Productie-klare console output

## [0.6.0] - 2025-12-07

### ✨ Toegevoegd - Vakantiemodus & Internationalisatie

**Eén-Klik Vakantiebeheer**
- **Vakantiemodus**: Zet alle zones op Weg preset voor langdurige periodes met één klik
  - Configureer datumbereik (start/eind datums) voor vakantieperiode
  - Kies preset modus (Weg, Eco, of Slapen) om toe te passen op alle zones
  - Vorstbescherming override met configureerbare minimumtemperatuur
  - Auto-uitschakelen wanneer iemand thuis komt (persoon entiteit integratie)
  - Visuele banner op dashboard wanneer vakantiemodus actief is
  - Service aanroepen voor automatisering integratie

**Backend Implementatie**
- Nieuwe `VacationManager` klasse beheert vakantiemodus status en zone overrides
- API endpoints: `GET/POST/DELETE /api/smart_heating/vacation_mode`
- Climate controller integratie: overschrijft automatisch zone presets tijdens vakantie
- WebSocket events broadcasten vakantiemodus wijzigingen in real-time
- Persistente opslag in `.storage/smart_heating/vacation_mode.json`

**Frontend Implementatie**
- Nieuwe **VacationModeSettings** component in Globale Instellingen pagina
  - Material-UI datum pickers voor start/eind datum selectie
  - Preset modus dropdown (Weg, Eco, Slapen)
  - Vorstbescherming toggle met minimumtemperatuur slider
  - Auto-uitschakelen toggle voor persoon entiteit integratie
  - Inschakelen/Uitschakelen knoppen met laadstatussen
- **VacationModeBanner** component toont actieve vakantiemodus op dashboard
  - Toont huidige preset modus en eind datum
  - Snelle uitschakelen knop voor gemakkelijke exit
  - Automatische verversing elke 30 seconden

**Service Aanroepen**
- `smart_heating.enable_vacation_mode` - Vakantiemodus inschakelen
  - Velden: start_date, end_date, preset_mode, frost_protection_override, min_temperature, auto_disable
- `smart_heating.disable_vacation_mode` - Vakantiemodus uitschakelen

**Gebruikssituaties**
- Zet gehele woning op energie-besparende modus voor vakanties
- Bescherm tegen bevriezing van leidingen tijdens winter vakanties
- Hervat automatisch normale verwarming bij thuiskomst
- Plan vakantiemodus via automatiseringen

**Meertalige Ondersteuning**
- **Internationalisatie (i18n)**: Volledig meertalige gebruikersinterface
  - Automatische taaldetectie van Home Assistant instellingen
  - Ondersteunde talen: Engels (English) en Nederlands (Dutch)
  - Handmatige taal wisseling via interface (🌍 knop in header)
  - Volledige UI vertaling inclusief:
    - Dashboard en zone kaarten
    - Alle instellingen pagina's
    - Formulieren en foutmeldingen
    - Vakantiemodus interface
    - Help teksten en tooltips
  - i18next framework voor robuuste vertaal beheer
  - Custom Home Assistant taal detector
  - Browser taal fallback mechanisme

**i18n Implementatie**
- Frontend: i18next + react-i18next + i18next-browser-languagedetector
- Vertaalbestanden: `src/locales/{en,nl}/translation.json`
- 200+ vertaal sleutels georganiseerd per functiedomein
- Custom taal detector controleert eerst Home Assistant localStorage
- Componenten bijgewerkt met `useTranslation` hook

### 🔧 Afhankelijkheden
- Toegevoegd `@mui/x-date-pickers` v7.22.2 voor datum selectie UI
- Toegevoegd `date-fns` v2.30.0 voor datum verwerking
- Toegevoegd `i18next` v23.16.11 voor internationalisatie
- Toegevoegd `react-i18next` v15.1.3 voor React integratie
- Toegevoegd `i18next-browser-languagedetector` v8.0.2 voor automatische taal detectie

### 📚 Documentatie
- Bijgewerkt README.md met Vakantiemodus functie beschrijving
- Bijgewerkt README.md met Internationalisatie functie beschrijving
- Bijgewerkt CHANGELOG.md met v0.6.0 release notities
- Vakantiemodus services toegevoegd aan services.yaml
- Nieuwe README.nl.md: Volledige Nederlandse vertaling van documentatie
- Nieuwe CHANGELOG.nl.md: Nederlandse vertaling van wijzigingslogboek
- E2E tests voor vakantiemodus (9 tests in vacation-mode.spec.ts)
- Test documentatie: VACATION_MODE_TEST_GUIDE.md

### 🧪 Testing
- E2E test suite voor vakantiemodus met 9 uitgebreide tests
- Test coverage: enable/disable flows, datum validatie, frost protection, UI states
- Tests verifiëren: API integratie, WebSocket updates, visuele componenten

## [0.5.7] - 2025-12-06

### 🐛 Kritieke Fixes

**Async Bestand I/O**
- Blokkerende bestand operaties gefixed in area logger
  - Alle bestand reads/writes gebruiken nu `hass.async_add_executor_job()`
  - Voorkomt event loop blokkering waarschuwingen
  - Verbeterde prestaties en responsiviteit

**API Rate Limiting Bescherming**
- Temperatuur wijziging detectie reeds aanwezig (v0.5.6+)
  - Zet alleen thermostaat temperatuur indien gewijzigd met ≥0.1°C
  - Voorkomt raken van Google Nest API rate limits
  - Gecachte laatst ingestelde temperatuur per thermostaat

**Uitgeschakelde Zone Afhandeling**
- Uitgeschakelde zones poging tot apparaat controle gefixed
  - Uitgeschakelde zones slaan nu ALLE apparaat controle over
  - Geen `climate.turn_off` fouten meer op MQTT apparaten
  - Apparaten behouden hun huidige status
  - Temperatuur tracking gaat normaal door

**Scheduler Opschoning**
- Onnodige climate service aanroep voor preset modi verwijderd
  - Preset modus direct ingesteld op zone object
  - Geen "Action climate.set_preset_mode not found" waarschuwingen meer
  - Schonere, efficiëntere schema activatie

**Learning Engine Parameter Fix**
- `async_predict_heating_time()` parameter mismatch gefixed
  - Gewijzigd `start_temp` → `current_temp`
  - Ongebruikte `outdoor_temp` parameter verwijderd
  - Slimme nacht boost voorspellingen werken correct

## [0.5.6] - 2025-12-06

### 🚀 Prestatie Verbeteringen - Bestand-Gebaseerde Logging

**Persistente Logging Opslag**
- Logs opgeslagen in aparte `.jsonl` bestanden per event type
  - Opslag locatie: `.storage/smart_heating/logs/{area_id}/{event_type}.jsonl`
  - Automatische rotatie bij 1.000 entries per bestand
  - Oude bestanden hernoemd met timestamp (bijv. `temperature.jsonl.1733123456`)
  - Logs blijven behouden na Home Assistant herstarts
- Event types: `temperature`, `heating`, `schedule`, `smart_boost`, `sensors`, `mode`

**Verbeterde Log Details**
- **Temperatuur bron tracking**: Log toont of temperatuur komt van preset, schema, of basis instelling
- **Nacht boost berekeningen**: Toont actuele boost waarde in logs (bijv. "Night boost: +2.0°C")
- Gedetailleerde JSON data voor elk log entry met exacte parameters
- Timestamp in ISO 8601 formaat voor eenvoudig sorteren

**Chip-Gebaseerde Filtering**
- **Eén-klik filters**: Klik op event type chip om alleen die logs te tonen
- **Visuele feedback**: Geselecteerde chips gemarkeerd met primaire kleur
- **Multi-selectie**: Klik meerdere chips om event types te combineren
- **Alles tonen**: Klik geselecteerde chip opnieuw om filter te verwijderen
- Event type kleuren:
  - 🌡️ Temperatuur (blauw)
  - 🔥 Verwarming (rood)
  - 📅 Schema (paars)
  - 🌙 Slimme Boost (indigo)
  - 📡 Sensoren (groen)
  - 🎯 Modus (oranje)

### 🐛 Bug Fixes

**Temperatuur Controle Precisie**
- Temperatuur wijziging detectie toegevoegd
  - Controleert alleen thermostaat temperatuur indien gewijzigd met ≥0.1°C
  - Voorkomt onnodige API aanroepen
  - Verbetert systeem responsiviteit
  - Beschermt tegen API rate limiting

**Manual Override Detectie**
- Externe thermostaat wijzigingen juist gedetecteerd
  - Systeem vergelijkt zone temperatuur met actuele thermostaat temperatuur
  - Automatisch schakelt naar MANUAL modus bij verschil
  - Herstelt automatisch wanneer thermostaat via app aangepast

## [0.5.5] - 2025-12-05

### 🐛 Bug Fixes

**Slimme Nacht Boost Reparatie**
- Gefixed `KeyError: 'last_predicted_start'` in nacht boost logica
  - Toegevoegd veilige dictionary toegang met `.get()`
  - Toegevoegd default waarden voor ontbrekende sleutels
  - Verbeterde fout afhandeling in voorspelling code

**Temperature Sensor Behandeling**
- Gefixed temperatuur sensor waarde extractie
  - Behandelt zowel `temperature` attribuut als `state` waarde
  - Correcte float conversie met fout afhandeling
  - Robustere sensor data verwerking

**Scheduler Tijdzone Fix**
- Correcte tijdzone afhandeling in schema vergelijkingen
  - Gebruikt Home Assistant's geconfigureerde tijdzone
  - Voorkomt onjuiste schema activatie door tijdzone verschil
  - Verbeterde schema logging met tijdzone info

### 📝 Logs & Debugging

**Verbeterde Area Logs**
- Toegevoegde logs voor:
  - Slimme nacht boost voorspelling start/stop
  - Schema activatie met tijdzone details
  - Temperatuur sensor waarde extractie
  - Manual override detectie
- Kleur-gecodeerde event types voor gemakkelijke visuele filtering
- JSON data weergave voor gedetailleerde inspectie

## [0.5.4] - 2025-12-04

### ✨ Nieuwe Functies

**Per-Area Ontwikkelings Logs**
- Nieuwe "Logs" tab in area detail pagina
- Toont alle verwarmingsstrategie beslissingen in chronologische volgorde
- Event types:
  - 🌡️ **Temperatuur**: Doel temperatuur wijzigingen (preset/schema/boost)
  - 🔥 **Verwarming**: Verwarmingsstatus wijzigingen (aan/uit/inactief)
  - 📅 **Schema**: Schema activaties en deactivaties
  - 🌙 **Slimme Boost**: Nacht boost voorspellingen en triggers
  - 📡 **Sensoren**: Raam sensor, aanwezigheids sensor triggers
  - 🎯 **Modus**: Manual override mode wijzigingen
- Kleur-gecodeerde chips voor gemakkelijke visuele filtering
- Gedetailleerde JSON data voor elk event
- Automatische scroll naar nieuwste logs
- Real-time updates via coordinator

**Verbeterde Manual Override Detectie**
- Detecteert externe thermostaat wijzigingen
- Automatisch schakelt naar MANUAL modus
- Real-time WebSocket updates
- Logging van mode wijzigingen

### 🛠️ Verbeteringen

**Backend Logging Systeem**
- Nieuwe `AreaLogger` klasse voor gestructureerde logging
- In-memory log opslag (100 entries per area)
- Event categorisatie en metadata
- API endpoint: `GET /api/smart_heating/area/{area_id}/logs`

**Frontend Logs Component**
- `AreaLogs.tsx`: Nieuwe component voor log weergave
- Event type filtering met chips
- Kleur-gecodeerde event types
- JSON data weergave in accordions
- Responsive layout met grid

### 📚 Documentatie
- Bijgewerkt README.md met Area Logs functie
- Toegevoegd logging documentatie
- Verbeterde troubleshooting sectie

## [0.5.3] - 2025-12-03

### ✨ Nieuwe Functies - Slimme Nacht Boost

**Schedule-Bewuste Nacht Boost**
- Nacht boost alleen actief wanneer GEEN schema actief is
- Schema's hebben altijd voorrang boven nacht boost
- Voorkomt conflicten tussen nacht boost en schema's

**Slimme Nacht Boost**
- Detecteert eerste ochtend schema (00:00-12:00)
- Leest schema's preset temperatuur als doel
- Voorspelt optimale start tijd gebaseerd op buitentemperatuur
- Start verwarmen op voorspeld moment
- Stopt wanneer schema activeert
- Gebruikt learning engine voor nauwkeurige voorspellingen

**Verbeterde Learning Engine**
- Nieuwe methode: `async_predict_heating_time()`
- Input: huidige temperatuur, doel temperatuur, outdoor temperatuur
- Output: voorspelde verwarmingstijd in uren
- Gebruikt linear regression op historische data
- Automatische data retentie en opschoning

### 🛠️ Verbeteringen

**Scheduler Logica**
- Verbeterde schema detectie logica
- Betere cross-day schema afhandeling
- Nauwkeurigere schema prioriteit

**Frontend**
- Nieuwe "Slimme Nacht Boost" toggle in Boost tab
- Toont voorspelde start tijd
- Visualiseert ochtend schema detectie

### 📚 Documentatie
- Bijgewerkt README.md met Slimme Nacht Boost uitleg
- Toegevoegd learning engine documentatie
- Verbeterde voorbeelden en use cases

## [0.5.2] - 2025-12-02

### 🐛 Bug Fixes

**Scheduler Cross-Day Support**
- Gefixed schema's die middernacht overschrijden
- Schema's kunnen nu correct dag overschrijden
- Voorbeeld: Zaterdag 22:00 - Zondag 07:00 werkt nu correct

**Preset Mode Schedules**
- Gefixed preset mode schema activatie
- Preset mode nu correct gezet op area
- Gebruikt globale preset temperaturen wanneer ingesteld

### 🛠️ Verbeteringen

**Frontend Schema Editor**
- Verbeterde validatie voor cross-day schema's
- Betere foutmeldingen
- Verbeterde UX voor schema creatie

## [0.5.1] - 2025-12-01

### 🐛 Bug Fixes

**API Learning Endpoint**
- Gefixed `learning_engine` data serialisatie fout
- Learning engine nu correct uitgefilterd van coordinator data
- API `/api/smart_heating/areas` werkt weer correct

### 🛠️ Verbeteringen

**Error Handling**
- Verbeterde fout afhandeling in API endpoints
- Betere logging voor debugging

## [0.5.0] - 2025-11-30

### ✨ Nieuwe Functies

**Preset Mode Schedules**
- Schema's kunnen nu preset modi instellen in plaats van vaste temperaturen
- Toggle tussen temperatuur-gebaseerd en preset-gebaseerd in schema editor
- Combineert met globale preset temperaturen voor maximale flexibiliteit

**Cross-Day Schedule Support**
- Schema's kunnen middernacht overschrijden
- Voorbeeld: Zaterdag 22:00 - Zondag 07:00
- Automatische dag-overschrijding detectie

**Globale Aanwezigheidssensoren**
- Configureer aanwezigheidssensoren eenmaal in globale instellingen
- Pas toe op alle zones met toggle
- Per-zone override optie beschikbaar
- Vereenvoudigt configuratie voor multi-zone setups

**Per-Area Aanwezigheid Toggle**
- Kies tussen globale of area-specifieke aanwezigheid per zone
- Flexibele configuratie voor verschillende zones
- Gemakkelijk schakelen tussen modi

### 🛠️ Verbeteringen

**Frontend**
- Nieuwe "Globale Aanwezigheidssensoren" tab in globale instellingen
- Verbeterde schema editor met preset mode ondersteuning
- Cross-day schema visuele indicators
- Betere aanwezigheid configuratie UI

**Backend**
- Verbeterde scheduler logica voor cross-day schema's
- Globale aanwezigheidssensor opslag
- Preset mode schema ondersteuning in database

### 📚 Documentatie
- Bijgewerkt README.md met nieuwe functies
- Verbeterde configuratie voorbeelden
- Toegevoegd schema gebruik voorbeelden

## [0.4.3] - 2025-11-28

### ✨ Nieuwe Functies

**Globale Preset Temperaturen**
- Configureer standaard temperaturen voor alle presets in één keer
- Nieuwe "Globale Preset Instellingen" tab in globale instellingen
- Per-area toggle om globale of aangepaste preset temperaturen te gebruiken
- Naadloos schakelen tussen globale en aangepaste modi

**Aanwezigheidsdetectie**
- Automatisch preset wisselen gebaseerd op aanwezigheid
- Ondersteunt Person entiteiten, Device Trackers, en bewegingssensoren
- Weg preset wanneer niemand thuis
- Thuis preset wanneer iemand arriveert
- Gebruikt uw geconfigureerde preset temperaturen

### 🛠️ Verbeteringen

**Frontend**
- Nieuwe GlobalPresetSettings component
- Nieuwe PresenceSensorSettings component
- Verbeterde GlobalSettings layout met tabs
- Betere visuele feedback voor preset configuratie

**Backend**
- Globale preset opslag in configuratie
- Aanwezigheidsdetectie logica
- Automatische preset mode wisseling

### 📚 Documentatie
- Bijgewerkt README.md met nieuwe functies
- Toegevoegd globale preset configuratie uitleg
- Verbeterde aanwezigheidsdetectie documentatie

---

*Voor volledige wijzigingsgeschiedenis, zie [CHANGELOG.md](CHANGELOG.md) (Engels)*
