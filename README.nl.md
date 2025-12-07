# Slimme Verwarming

Een Home Assistant custom integratie voor het beheren van verwarmingssystemen met meerdere zones via Zigbee2MQTT apparaten. Bevat een moderne React-gebaseerde webinterface voor eenvoudige zone configuratie en apparaatbeheer.

## ✨ Functies

- 🏠 **Multi-zone verwarmingsregeling** - Creëer en beheer meerdere verwarmingszones
- 🌡️ **Universele Apparaatondersteuning** - Werkt met ALLE Home Assistant climate integraties
  - Google Nest, Ecobee, generic_thermostat, MQTT/Zigbee2MQTT, en ELKE climate entiteit
  - Platform-onafhankelijke apparaat ontdekking
  - Geen integratie-specifieke code vereist
- 🎛️ **Web-gebaseerde GUI** - Moderne React interface met intelligent apparaatbeheer
  - Locatie-gebaseerde apparaat filtering
  - Directe apparaat toewijzing vanaf zone pagina's
  - Real-time apparaat status updates
- 🔄 **Handmatige Override Modus** - Automatische detectie van externe thermostaat wijzigingen (NIEUW in v0.4.0)
  - Systeem detecteert wanneer thermostaat buiten app aangepast wordt (bijv. Google Nest draaiknop)
  - Gaat in "HANDMATIG" modus - app stopt met regelen, behoudt gebruiker's instelling
  - Real-time updates binnen 2-3 seconden via WebSocket
  - Wordt automatisch gewist wanneer temperatuur via app aangepast wordt
  - Blijft behouden na herstarts
- 📅 **Slim Plannen** - Tijdgebaseerde temperatuur profielen met dag-van-de-week selectie
  - **Preset Modus Schema's** - Stel preset modi in (Weg, Eco, Comfort, etc.) in plaats van vaste temperaturen (v0.5.0+)
  - **Dag-overschrijdende Ondersteuning** - Schema's kunnen middernacht overschrijden (bijv. Zaterdag 22:00 - Zondag 07:00) (v0.5.0+)
  - Schakel tussen temperatuur-gebaseerd en preset-gebaseerd plannen
  - Combineer met globale preset temperaturen voor maximale flexibiliteit
- 🌙 **Nacht Boost** - Configureerbare temperatuur verhoging tijdens nachtelijke uren (aanpasbare start/eind tijden)
  - **Schema-Bewust** - Coördineert automatisch met actieve schema's (v0.5.3+)
  - Alleen actief wanneer GEEN schema actief is (schema's hebben voorrang)
  - Werkt als voorverwarmingsmechanisme voor ochtend schema's
- 🧠 **Adaptief Leren** - Machine learning systeem dat verwarmingspatronen en weer correlatie leert
  - Voorspelt automatisch verwarmingstijd gebaseerd op buitentemperatuur
  - **Slimme nacht boost** - Detecteert ochtend schema's en verwarmt daar naartoe (v0.5.3+)
  - Leest eerste ochtend schema (00:00-12:00) als doeltijd
  - Gebruikt schema's preset temperatuur als verwarmingsdoel
  - Start verwarmen op optimaal voorspeld moment voor schema
  - Gebruikt Home Assistant Statistics API voor efficiënte database opslag
  - Volgt verwarmingssnelheden, afkoelsnelheden, en buitentemperatuur correlaties
- 🎯 **Preset Modi** - Snelle temperatuur presets (WEG, ECO, COMFORT, THUIS, SLAPEN, ACTIVITEIT, BOOST)
  - **Globale Preset Temperaturen** - Configureer standaard temperaturen voor alle zones (v0.4.3+)
  - **Per-Zone Aanpassing** - Kies tussen globale standaarden of aangepaste temperaturen per zone
  - Naadloos schakelen tussen globale en aangepaste instellingen met toggle controls
- ⚡ **Boost Modus** - Tijdelijke hoge-temperatuur boost met configureerbare duur
- 🪟 **Raam Sensor Integratie** - Configureerbare acties (uitschakelen, temperatuur verlagen, of geen) wanneer ramen/deuren opengaan met aangepaste temperatuur verlagingen
- 👤 **Aanwezigheidsdetectie** - Automatische preset modus wisseling gebaseerd op aanwezigheid (v0.4.3+)
  - Schakelt naar "Weg" preset wanneer niemand thuis is
  - Keert terug naar "Thuis" preset wanneer iemand arriveert
  - Werkt met Persoon entiteiten, Apparaat Trackers, en bewegingssensoren
  - Geen handmatige temperatuur aanpassingen - gebruikt uw geconfigureerde preset temperaturen
  - **Globale Aanwezigheidssensoren** - Configureer sensoren eenmaal, pas toe op alle zones (v0.5.0+)
  - **Per-Zone Toggle** - Kies globale of zone-specifieke aanwezigheidsdetectie per zone (v0.5.0+)
- 🔌 **Slimme Schakelaar Controle** - Per-zone controle om schakelaars/pompen uit te schakelen wanneer niet verwarmt (v0.4.2+)
  - Energie efficiënt: Schakelt circulatiepompen automatisch uit wanneer verwarmen stopt
  - Altijd-aan modus: Houd pompen continu aan voor systemen die constante circulatie vereisen
  - Werkt in handmatige override modus: Schakelaars gecontroleerd gebaseerd op actuele thermostaat verwarmingsstatus
- ❄️ **Vorstbescherming** - Globale minimumtemperatuur om bevriezing te voorkomen
- 🌡️ **HVAC Modi** - Ondersteuning voor verwarmen, koelen, auto, en uit modi
- 📋 **Schema Kopiëren** - Dupliceer schema's tussen zones en dagen
- 📊 **Temperatuur Geschiedenis** - Volg en visualiseer temperatuur trends met interactieve grafieken
  - Configureerbare bewaartermijn (1-365 dagen, standaard 30 dagen)
  - Aangepaste tijdsbereik selectie met datum/tijd picker
  - Preset bereiken: 6u, 12u, 24u, 3d, 7d, 30d
  - 5-minuten data resolutie (nooit geaggregeerd)
  - Automatische opschoning elk uur
- 📝 **Ontwikkelings Logs** - Per-zone logging systeem voor debugging en zichtbaarheid (v0.5.4+)
  - Toegewijde Logs tab in zone details met alle verwarmingsstrategie beslissingen
  - Kleur-gecodeerde event types: Temperatuur, Verwarming, Schema, Slimme Boost, Sensoren, Modus Wijzigingen
  - Gedetailleerde JSON data voor elke log entry met exacte parameters
  - **Chip-Gebaseerde Filtering** - Eén-klik event type filters met visuele feedback (v0.5.6+)
  - **Bestand-Gebaseerde Opslag** - Persistente logs opgeslagen in aparte `.jsonl` bestanden per event type (v0.5.6+)
    - Opslag: `.storage/smart_heating/logs/{area_id}/{event_type}.jsonl`
    - Automatische rotatie bij 1.000 entries per bestand
    - Logs blijven behouden na Home Assistant herstarts
  - Volgt: temperatuur wijzigingen, verwarmingsstatus wijzigingen, schema activeringen, slimme nacht boost voorspellingen, sensor triggers, handmatige override modus
  - **Verbeterd Detail** - Temperatuur bron tracking (preset/schema/basis), nacht boost berekeningen met waarden (v0.5.6+)
- ⚙️ **Geavanceerde Instellingen** - Hysterese controle, temperatuur limieten, en fine-tuning
  - **Globale Hysterese** - Stel standaard temperatuur buffer in om snel aan/uit schakelen te voorkomen (0.1-2.0°C)
  - **Zone-Specifieke Hysterese Override** - Pas hysterese per zone aan (NIEUW in v0.3.18)
    - Nuttig voor vloerverwarmingssystemen (kan 0.1-0.3°C gebruiken)
    - Help modal legt hysterese uit en geeft systeem-specifieke aanbevelingen
    - Schakel tussen globale instelling of aangepaste waarde
  - **Tabblad Globale Instellingen** - Georganiseerde interface met 4 categorieën (NIEUW in v0.3.18)
    - 🌡️ Temperatuur: Globale voorinstellingstemperaturen
    - 👥 Sensoren: Globale aanwezigheidssensor configuratie
    - 🏖️ Vakantie: Vakantiemodus instellingen
    - ⚙️ Geavanceerd: Hysterese en toekomstige geavanceerde functies
- 🌐 **REST API** - Volledige API voor programmatische controle
- 📡 **WebSocket ondersteuning** - Real-time updates en status synchronisatie
- 🎛️ **Climate entiteiten** - Volledige thermostaat controle per zone
- 🔌 **Schakelaar entiteiten** - Eenvoudige zone aan/uit controle
- 📊 **Sensor entiteiten** - Systeem status monitoring
- 🛠️ **Service aanroepen** - Uitgebreide service API voor automatisering
- 💾 **Persistente opslag** - Configuratie en geschiedenis automatisch opgeslagen
- 🔄 **Auto-update** - Data coordinator met 30-seconden interval
- 📝 **Debug logging** - Uitgebreide logging voor probleemoplossing
- 🏖️ **Vakantiemodus** - Eén-klik modus om alle zones op Weg preset te zetten (NIEUW in v0.6.0)
  - Stel datumbereik in voor langdurige afwezigheden
  - Auto-uitschakelen wanneer iemand thuis komt
  - Vorstbescherming met minimum temperatuur override
  - Visuele banner en snelle uitschakeling
- 🌍 **Internationalisatie** - Meertalige ondersteuning (Engels en Nederlands) (NIEUW in v0.6.0)
  - Automatische taaldetectie van Home Assistant instellingen
  - Handmatige taal wisseling via interface
  - Volledige UI vertaling

## 🚀 Komende Functies in v0.6.0+

**Status**: Vakantiemodus en Internationalisatie Uitgebracht! Aanvullende functies in ontwikkeling.

## 📋 Vereisten

- Home Assistant 2023.1.0 of nieuwer
- Python 3.11+
- Climate entiteiten (thermostaten) geconfigureerd in Home Assistant
- (Optioneel) Temperatuur sensoren voor nauwkeurigere controle
- (Optioneel) Raam/deur sensoren voor automatisering

## 🔧 Installatie

### HACS (Aanbevolen)

1. Open HACS in uw Home Assistant instantie
2. Klik op "Integraties"
3. Klik op de drie puntjes in de rechterbovenhoek
4. Selecteer "Aangepaste repositories"
5. Voeg deze repository URL toe: `https://github.com/ralf1975/smart_heating`
6. Selecteer categorie: "Integratie"
7. Klik "Toevoegen"
8. Zoek naar "Smart Heating" in HACS
9. Klik "Installeren"
10. Herstart Home Assistant

### Handmatige Installatie

1. Download de nieuwste release van deze repository
2. Pak het archief uit
3. Kopieer de `custom_components/smart_heating` map naar uw `<config_dir>/custom_components/` directory
4. Herstart Home Assistant

## ⚙️ Configuratie

### Via UI (Aanbevolen)

1. Ga naar Home Assistant Instellingen → Apparaten & Services
2. Klik op "Integratie Toevoegen"
3. Zoek naar "Smart Heating"
4. Volg de configuratie wizard

De integratie zal automatisch:
- Alle zones detecteren (Home Assistant zones)
- Climate entiteiten per zone ontdekken
- Standaard instellingen initialiseren

### Handmatige Configuratie (configuration.yaml)

```yaml
smart_heating:
  # Globale instellingen
  frost_protection_temp: 5.0
  default_hysteresis: 0.5
  
  # Zones worden automatisch gedetecteerd
  # Gebruik de web UI voor zone configuratie
```

## 💻 Web Interface Toegang

Na installatie, toegang tot de web interface via:

**URL**: `http://YOUR_HOME_ASSISTANT:8123/api/smart_heating/`

Of voeg een panel toe aan uw sidebar:

```yaml
panel_iframe:
  smart_heating:
    title: "Slimme Verwarming"
    url: "/api/smart_heating/"
    icon: mdi:thermostat
    require_admin: false
```

## 📱 Gebruik

### Dashboard Overzicht

Het hoofddashboard toont alle geconfigureerde zones met:
- Huidige en doel temperaturen
- Verwarmingsstatus (verwarmt/inactief/uit)
- Handmatige override indicator
- Actieve preset modus
- Snelle temperatuur aanpassing sliders
- Apparaat lijst met real-time status

### Zone Beheer

#### Zone Aanmaken

Zones worden automatisch gedetecteerd van uw Home Assistant zone configuratie.

#### Apparaten Toevoegen aan Zones

**Methode 1: Directe Selectie**
1. Klik op een zone kaart om zone details te openen
2. Ga naar de "Apparaten" tab
3. Klik "Apparaat Toevoegen"
4. Selecteer apparaten uit de gefilterde lijst (alleen apparaten in dezelfde locatie)

**Methode 2: Sleep & Drop** (van alle apparaten)
1. Scroll naar de "Alle Apparaten" sectie onderaan het dashboard
2. Sleep een apparaat naar een zone kaart
3. Laat los om toe te wijzen

#### Apparaten Verwijderen

1. Open zone details
2. Ga naar de "Apparaten" tab
3. Klik het verwijder icoon (🗑️) naast een apparaat

### Temperatuur Controle

#### Handmatige Controle

1. Gebruik de slider op een zone kaart voor directe aanpassing
2. Temperatuur wordt onmiddellijk ingesteld
3. Schakelt automatisch naar handmatige override modus

#### Preset Modi

1. Klik op een zone kaart
2. Selecteer een preset modus:
   - **WEG**: Lagere temperatuur voor lege zones
   - **ECO**: Energie besparing
   - **COMFORT**: Normale comfortabele temperatuur
   - **THUIS**: Standaard aanwezigheidstemperatuur
   - **SLAPEN**: Nacht temperatuur
   - **ACTIVITEIT**: Hogere temperatuur voor actieve ruimtes
   - **BOOST**: Maximum temperatuur

#### Globale Preset Temperaturen (v0.4.3+)

Configureer standaard temperaturen voor alle zones:

1. Klik de instellingen knop (⚙️) in de header
2. Ga naar de "Globale Preset Instellingen" tab
3. Stel temperaturen in voor elke preset modus
4. Wijzigingen worden automatisch opgeslagen

**Per-Zone Customisatie**:
- Elk zone kan kiezen tussen globale presets of aangepaste temperaturen
- Gebruik de "Gebruik Globale Presets" toggle in zone preset instellingen
- Schakel naadloos tussen globale en aangepaste modi

### Planning

#### Een Programma Aanmaken

1. Open zone details
2. Ga naar de "Planning" tab
3. Klik "Programma Toevoegen"
4. Stel in:
   - Dagen van de week
   - Start tijd
   - Eind tijd (kan dag overschrijden)
   - Preset modus OF doel temperatuur
5. Klik "Opslaan"

#### Schema Types (v0.5.0+)

**Temperatuur-gebaseerd**: Stel exacte temperatuur in voor schema periode
**Preset-gebaseerd**: Gebruik preset modus (combineert met globale preset temperaturen)

#### Schema's Kopiëren

1. Open zone details
2. Ga naar de "Planning" tab
3. Klik "Schema Kopiëren"
4. Selecteer bron zone en dag
5. Selecteer doel dag(en)
6. Klik "Kopiëren"

### Boost Modus

Tijdelijk verhogen van temperatuur:

1. Klik op een zone kaart
2. Klik "Boost" knop
3. Stel doel temperatuur en duur in
4. Klik "Start Boost"

Boost eindigt automatisch na de ingestelde duur.

### Nacht Boost

Automatische temperatuur verhoging tijdens nacht uren:

1. Open zone details
2. Ga naar de "Boost" tab
3. Schakel "Nacht Boost" in
4. Stel in:
   - Start tijd (standaard 22:00)
   - Eind tijd (standaard 06:00)
   - Temperatuur verhoging (standaard +2°C)

**Schema-Bewuste Werking (v0.5.3+)**:
- Nacht boost alleen actief wanneer GEEN schema actief is
- Schema's hebben altijd voorrang
- Werkt als voorverwarming voor ochtend schema's
- Slimme nacht boost voorspelt optimale start tijd

### Slimme Nacht Boost (v0.5.3+)

Automatische optimalisatie van ochtend verwarming:

1. Schakel "Slimme Nacht Boost" in in zone boost instellingen
2. Systeem zal:
   - Eerste ochtend schema detecteren (00:00-12:00)
   - Buitentemperatuur lezen
   - Optimale start tijd voorspellen
   - Verwarmen naar schema's preset temperatuur
   - Stoppen wanneer schema activeert

**Hoe het Werkt**:
- Gebruikt machine learning om verwarmingssnelheden te leren
- Correleert verwarmingstijd met buitentemperatuur
- Verbetert voorspellingen in de tijd
- Alleen actief wanneer geen schema actief is

### Adaptief Leren

Het systeem leert automatisch:

**Wat het leert**:
- Verwarmingssnelheid (graden per uur)
- Afkoelingssnelheid
- Buitentemperatuur correlatie
- Optimale voorverwarmingstijd

**Data Opslag**:
- Gebruikt Home Assistant Statistics API
- Efficiënte database opslag
- Automatische data retentie
- Geen handmatige configuratie nodig

**Voorspellingen Bekijken**:
1. Open zone details
2. Ga naar de "Leren" tab
3. Bekijk:
   - Huidige leerstatistieken
   - Voorspelde verwarmingstijd
   - Buitentemperatuur correlatie

### Raam Sensor Integratie

Automatische acties wanneer ramen/deuren opengaan:

1. Open zone details
2. Ga naar de "Sensoren" tab
3. Schakel "Raam Sensor Integratie" in
4. Selecteer actie:
   - **Uitschakelen**: Volledige verwarming uit
   - **Temperatuur Verlagen**: Verlaag met aangepast bedrag
   - **Geen**: Alleen monitoren
5. Selecteer sensor entiteiten
6. (Als verlagen) Stel temperatuur verlaging in

### Aanwezigheidsdetectie

Automatisch preset wisselen gebaseerd op aanwezigheid:

#### Globale Configuratie (v0.5.0+)

1. Klik instellingen knop (⚙️) in header
2. Ga naar "Globale Aanwezigheidssensoren" tab
3. Selecteer persoon entiteiten of device trackers
4. Alle zones met globale aanwezigheid ingeschakeld zullen deze gebruiken

#### Per-Zone Configuratie

1. Open zone details
2. Ga naar de "Sensoren" tab
3. Schakel "Aanwezigheidsdetectie" in
4. Kies bron:
   - **Globale Sensoren**: Gebruik globaal geconfigureerde sensoren
   - **Zone Sensoren**: Gebruik zone-specifieke sensoren
5. (Als zone sensoren) Selecteer sensor entiteiten

**Gedrag**:
- Niemand thuis → Schakelt naar WEG preset
- Iemand komt thuis → Schakelt naar THUIS preset
- Gebruikt uw geconfigureerde preset temperaturen

### Slimme Schakelaar Controle (v0.4.2+)

Automatische pomp/schakelaar controle:

1. Open zone details
2. Ga naar de "Sensoren" tab
3. Schakel "Slimme Schakelaar Controle" in
4. Selecteer schakelaar entiteiten (bijv. circulatiepompen)
5. Kies modus:
   - **Auto**: Schakel uit wanneer niet verwarmt
   - **Altijd Aan**: Houd continu aan

**Energie Besparing**:
- Auto modus schakelt pompen uit tijdens inactief
- Werkt in handmatige override modus
- Gebaseerd op werkelijke thermostaat verwarmingsstatus

### Vakantiemodus (v0.6.0+)

Eén-klik modus voor langdurige afwezigheden:

1. Klik instellingen knop (⚙️) in header
2. Ga naar "Vakantiemodus" tab
3. Stel configuratie in:
   - Start datum
   - Eind datum
   - Preset modus (Weg/Eco/Slapen)
   - Vorstbescherming (optioneel minimum temperatuur)
   - Auto-uitschakelen bij thuiskomst
4. Klik "Vakantiemodus Inschakelen"

**Functies**:
- Zet ALLE zones op geselecteerde preset
- Visuele banner op dashboard wanneer actief
- Optionele vorstbescherming override
- Automatisch uitschakelen bij aankomst personen
- Snelle uitschakeling via banner

**Uitschakelen**:
- Klik "Uitschakelen" op dashboard banner
- OF ga naar Vakantiemodus instellingen en klik "Uitschakelen"
- Automatisch uitschakelen wanneer iemand thuis komt (indien ingeschakeld)

### Taal Wisseling (v0.6.0+)

De interface ondersteunt meerdere talen:

**Automatische Detectie**:
- Detecteert uw Home Assistant taal instelling
- Schakelt automatisch naar ondersteunde taal (Engels/Nederlands)
- Valt terug op Engels indien taal niet ondersteund

**Handmatige Wijziging**:
1. Klik taal knop (🌍) in header
2. Selecteer gewenste taal:
   - English
   - Nederlands

**Ondersteunde Talen**:
- 🇬🇧 Engels (English)
- 🇳🇱 Nederlands (Dutch)

## 🔌 Entiteiten

De integratie creëert de volgende entiteiten per zone:

### Climate Entiteiten

- `climate.smart_heating_[zone_naam]`
  - Volledige thermostaat controle
  - Ondersteunde functies:
    - Doel temperatuur
    - HVAC modus (verwarmen/koelen/auto/uit)
    - Preset modi
    - Huidige temperatuur (indien sensor beschikbaar)
    - HVAC actie (verwarmt/inactief)

### Schakelaar Entiteiten

- `switch.smart_heating_[zone_naam]`
  - Eenvoudige aan/uit controle
  - Schakelt tussen "verwarmen" en "uit" modi
  - Handiger voor eenvoudige automatiseringen

### Sensor Entiteiten

Verschillende sensoren per zone:
- Doel temperatuur sensor
- Huidige temperatuur sensor
- Verwarmingsstatus sensor
- Actieve preset sensor
- En meer...

## 🛠️ Services

De integratie biedt verschillende services voor automatisering.

### `smart_heating.set_temperature`

Stel zone temperatuur in.

```yaml
service: smart_heating.set_temperature
data:
  area_id: woonkamer
  temperature: 21.5
```

### `smart_heating.set_preset_mode`

Stel zone preset modus in.

```yaml
service: smart_heating.set_preset_mode
data:
  area_id: woonkamer
  preset_mode: comfort
```

### `smart_heating.enable_boost`

Start boost modus.

```yaml
service: smart_heating.enable_boost
data:
  area_id: woonkamer
  temperature: 24.0
  duration: 120  # minuten
```

### `smart_heating.enable_vacation_mode`

Schakel vakantiemodus in voor alle zones.

```yaml
service: smart_heating.enable_vacation_mode
data:
  preset_mode: away
  start_date: "2024-07-01"
  end_date: "2024-07-14"
  enable_frost_protection: true
  frost_protection_temp: 7.0
  auto_disable_on_arrival: true
```

### `smart_heating.disable_vacation_mode`

Schakel vakantiemodus uit.

```yaml
service: smart_heating.disable_vacation_mode
```

Zie de [Services documentatie](docs/nl/services.md) voor volledige service referentie.

## 🔧 Geavanceerde Configuratie

### Hysterese

Hysterese voorkomt frequent schakelen van verwarming:

1. Open zone details
2. Ga naar "Instellingen" tab
3. Pas "Hysterese" aan (standaard 0.5°C)

**Hoe het werkt**:
- Verwarming start wanneer temperatuur < (doel - hysterese)
- Verwarming stopt wanneer temperatuur > doel
- Grotere hysterese = minder schakelacties, maar grotere temperatuur schommelingen

### Temperatuur Limieten

Stel minimum en maximum temperaturen in:

1. Open zone details
2. Ga naar "Instellingen" tab
3. Stel in:
   - Minimum temperatuur (standaard 5°C)
   - Maximum temperatuur (standaard 30°C)

### Vorstbescherming

Globale minimum temperatuur voor alle zones:

1. Klik instellingen knop (⚙️) in header
2. Zoek "Vorstbescherming Temperatuur"
3. Stel minimum temperatuur in (standaard 5°C)

Dit overschrijft alle zone instellingen om bevriezing te voorkomen.

## 📊 REST API

Volledige REST API beschikbaar op:

**Basis URL**: `/api/smart_heating/`

### Endpoints

#### GET `/api/smart_heating/areas`
Haal alle zones op met apparaten en instellingen.

#### GET `/api/smart_heating/devices`
Haal alle beschikbare apparaten op.

#### POST `/api/smart_heating/area/{area_id}/temperature`
Stel zone temperatuur in.

```json
{
  "temperature": 21.5
}
```

#### POST `/api/smart_heating/area/{area_id}/preset`
Stel preset modus in.

```json
{
  "preset_mode": "comfort"
}
```

Zie de [API Documentatie](docs/nl/api.md) voor volledige endpoint referentie.

## 🐛 Probleemoplossing

### Logs Controleren

Schakel debug logging in:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_heating: debug
```

### Veelvoorkomende Problemen

**Apparaten verschijnen niet in zone**:
- Controleer of apparaat een climate entiteit is
- Verifieer apparaat is toegewezen aan juiste Home Assistant zone
- Probeer Home Assistant opnieuw te starten

**Planning werkt niet**:
- Controleer tijdzone instellingen in Home Assistant
- Verifieer schema overlappingen
- Controleer dat zone niet in handmatige override modus is

**Preset modi werken niet**:
- Zorg dat preset temperaturen geconfigureerd zijn
- Controleer dat zone niet in boost modus is
- Verifieer dat schema's niet actief zijn (schema's hebben voorrang)

**WebSocket updates werken niet**:
- Controleer browser console voor fouten
- Verifieer Home Assistant WebSocket verbinding
- Probeer pagina te verversen (hard refresh: Ctrl+Shift+R)

**Vakantiemodus activeert niet**:
- Controleer dat datums correct ingesteld zijn
- Verifieer preset modus geldig is
- Controleer logs voor fouten

## 🤝 Bijdragen

Bijdragen zijn welkom! Zie [DEVELOPER.md](DEVELOPER.md) voor ontwikkelaars documentatie.

## 📄 Licentie

Dit project is gelicentieerd onder de MIT Licentie - zie het [LICENSE](LICENSE) bestand voor details.

## 🙏 Dankbetuigingen

- Home Assistant gemeenschap voor de geweldige documentatie
- Alle contributors en testers

## 📞 Ondersteuning

- **Issues**: [GitHub Issues](https://github.com/ralf1975/smart_heating/issues)
- **Discussies**: [GitHub Discussions](https://github.com/ralf1975/smart_heating/discussions)
- **Documentatie**: [Wiki](https://github.com/ralf1975/smart_heating/wiki)
