# Wijzigingslogboek

Alle belangrijke wijzigingen aan dit project worden gedocumenteerd in dit bestand.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
en dit project volgt [Semantic Versioning](https://semver.org/).

## [Niet Uitgebracht]

### ✨ Toegevoegd

**Gebied-Specifieke Hysterese Override (v0.3.18)**
- **Hysterese Aanpassing**: Gebieden kunnen nu de globale hysterese instelling overschrijven
  - Schakel tussen globale hysterese (standaard 0.5°C) of gebied-specifieke waarde
  - Bereik: 0.1°C tot 2.0°C met 0.1°C stappen
  - Bijzonder nuttig voor vloerverwarming systemen (kan 0.1-0.3°C gebruiken)
  - Help modal met gedetailleerde uitleg over hysterese en verwarmingssysteem types
  - Optimistische UI updates voor directe feedback
  - Status blijft behouden bij pagina verversing

**Globale Instellingen Herontwerp (v0.3.18)**
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
