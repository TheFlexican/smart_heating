# Architectuur Overzicht

Smart Heating is een Home Assistant integratie met een moderne web-gebaseerde interface voor het beheren van multi-zone verwarmingssystemen.

## Codekwaliteit & Standaarden

**SonarQube Analyse** (v0.4.1+)

De codebase ondergaat regelmatige SonarQube analyse om hoge codekwaliteitsnormen te handhaven:

- **Alle kritieke problemen opgelost**: Geen onbereikbare code, ongebruikte variabelen of blanco except clausules
- **Constanten geëxtraheerd**: Dubbele string literals vervangen door benoemde constanten voor onderhoudbaarheid
- **Hulpmethoden**: Complexe functies gerefactored met geëxtraheerde hulpmethoden om cognitieve complexiteit te verminderen
- **Type veiligheid**: Python 3.9+ compatibele type hints met `Optional[]` syntax
- **Resterende waarschuwingen**: Ontwerpkeuzes (async interfaces) of false positives (Home Assistant imports)

**Belangrijke Code Patronen:**
- `ERROR_*` constanten voor consistente foutmeldingen over API endpoints
- `ENDPOINT_PREFIX_*` constanten voor onderhoudbare routing
- Hulpmethoden zoals `_validate_time_format()`, `_determine_mqtt_device_type()` voor code hergebruik
- Uitgebreide validatie met duidelijke foutmeldingen

## Architectuur op Hoog Niveau

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Smart Heating Integratie                       │ │
│  │                                                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │ │
│  │  │ Area Manager │  │ Coordinator  │  │  Platforms  │   │ │
│  │  │   (Opslag)   │  │  (30s poll)  │  │ (Entiteiten)│   │ │
│  │  └──────┬───────┘  └──────┬───────┘  └─────────────┘   │ │
│  │         │                 │                            │ │
│  │  ┌──────┴─────────────────┴──────-────────────────┐    │ │
│  │  │   REST API (api.py + api_handlers/)            │    │ │
│  │  │   WebSocket API (websocket.py)                 │    │ │
│  │  │   Service Handlers (ha_services/)              │    │ │
│  │  │   (/api/smart_heating/*)                       │    │ │
│  │  │                                                │    │ │
│  │  └───────────────────────┬────────────────────────┘    │ │
│  │                          │                             │ │
│  │  ┌───────────────────────┴──────────────────────────┐  │ │
│  │  │                                                  │  │ │
│  │  │         Statische Bestand Server                 │  │ │
│  │  │    (/smart_heating/* → frontend/dist)            │  │ │
│  │  │                                                  │  │ │
│  │  └─────────────────────┬─--─────────────────────────┘  │ │
│  └────────────────────────┼───--──────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
             ┌──────────────────────────────┐
             │     React Frontend (SPA)     │
             │                              │
             │  - Zone Beheer UI            │
             │  - Apparaat Paneel           │
             │  - Real-time Updates         │
             │  - Material-UI Componenten   │
             └──────────────────────────────┘
                            │
                            │ MQTT (via HA)
                            ▼
             ┌──────────────────────────────┐
             │       Zigbee2MQTT            │
             │                              │
             │  - Thermostaten              │
             │  - Temperatuur Sensoren      │
             │  - OpenTherm Gateways        │
             │  - Radiator Kleppen          │
             └──────────────────────────────┘
```

## Backend Componenten

### 1. Area Manager (`area_manager.py`)

Kern bedrijfslogica voor het beheren van verwarmingszones.

**Verantwoordelijkheden:**
- Zone CRUD operaties
- Apparaat toewijzing aan zones
- Schema beheer (Schedule class)
- Nacht boost configuratie per zone
- Temperatuur controle en effectieve doel berekening
- Zone in-/uitschakelen
- Persistente opslag (via HA storage API)

**Data Model:**
```python
Area:
  - area_id: str
  - name: str
  - target_temperature: float
  - enabled: bool
  - hidden: bool
  - manual_override: bool  # v0.4.0+ - Gaat in handmatige modus wanneer thermostaat extern gewijzigd
  - devices: Dict[str, Device]
  - schedules: Dict[str, Schedule]
  - state: ZoneState (heating/idle/off/manual)
  - night_boost_enabled: bool
  - night_boost_offset: float
  - current_temperature: Optional[float]

Schedule:
  - schedule_id: str
  - time: str (HH:MM) [legacy]
  - day: str (Monday, Tuesday, etc.) [legacy - enkele dag]
  - days: List[str] (Monday, Tuesday, etc.) [v0.4.0+ - meerdaagse selectie]
  - date: str (JJJJ-MM-DD) [v0.4.0+ - datumspecifieke schema's]
  - start_time: str (HH:MM)
  - end_time: str (HH:MM)
  - temperature: float
  - preset_mode: str (optioneel - away, eco, comfort, home, sleep, activity)
  - enabled: bool

Schema Types (v0.4.0+):
  - Wekelijks Terugkerend: Gebruikt 'days' array voor meerdaagse schema's
  - Datumspecifiek: Gebruikt 'date' veld voor eenmalige schema's (feestdagen, evenementen)
  - Legacy: Enkel 'day' veld (achterwaarts compatibel)

Device:
  - id: str
  - type: str (thermostat/temperature_sensor/switch/valve/opentherm_gateway)
  - mqtt_topic: Optional[str]
  - entity_id: Optional[str]
```

**Ondersteunde Apparaat Types:**
- **thermostat** - Climate entiteiten van ELKE Home Assistant integratie
  - Google Nest, Ecobee, generic_thermostat, MQTT/Zigbee2MQTT, Z-Wave, etc.
  - Platform-onafhankelijk: Werkt met climate entiteiten van elke bron
  - Geen integratie-specifieke code vereist
- **temperature_sensor** - Externe sensoren voor zone monitoring
  - Flexibele detectie: device_class, unit_of_measurement, of entiteit naming
  - Werkt met sensor entiteiten van ELK platform
- **switch** - Per-zone circulatie pompen/relais
  - Slimme filtering voor verwarmings-gerelateerde schakelaars
- **valve** - TRV's met positie of temperatuur controle
  - Dynamische capability detectie tijdens runtime
- **opentherm_gateway** - Globale ketel controle (gedeeld over zones)

**Belangrijke Methoden:**
- `get_effective_target_temperature()` - Berekent doel met schema's + nacht boost
- `get_active_schedule_temperature()` - Vindt huidig actief schema
- `add_schedule()` / `remove_schedule()` - Schema beheer
- `get_switches()` - Haal schakelaar apparaten in zone op (NIEUW)
- `get_valves()` - Haal klep apparaten in zone op (NIEUW)
- `set_opentherm_gateway()` - Configureer globale OpenTherm gateway (NIEUW)
- `set_trv_temperatures()` - Stel TRV verwarmings-/inactieve temperaturen in (NIEUW)

### 2. Coordinator (`coordinator.py`)

Data update coordinator gebruikt Home Assistant's `DataUpdateCoordinator`.

**Verantwoordelijkheden:**
- Zone data ophalen elke 30 seconden
- Updates broadcasten naar entiteiten
- Vernieuw verzoeken afhandelen
- **Thermostaat status wijzigingen real-time monitoren** (v0.4.0+)
- **Automatische handmatige override detectie** (v0.4.0+)

**Handmatige Override Systeem** (v0.4.0+):

Detecteert wanneer thermostaten buiten de Smart Heating app aangepast worden en gaat automatisch in handmatige override modus.

**Componenten:**
1. **Status Wijziging Listeners** (`async_setup()`):
   - Registreert `async_track_state_change_event` voor alle climate entiteiten
   - Monitort `temperature` en `hvac_action` attribuut wijzigingen
   - Filtert app-geïnitieerde wijzigingen via `_ignore_next_state_change` flag

2. **Debouncing** (`_handle_state_change()`):
   - 2-seconden vertraging (configureerbaar via `MANUAL_TEMP_CHANGE_DEBOUNCE`)
   - Voorkomt vloedgolf van updates bij snelle draaiknop aanpassingen (bijv. Google Nest)
   - Annuleert vorige wachtende updates wanneer nieuwe wijzigingen gedetecteerd

3. **Handmatige Override Activatie** (`debounced_temp_update()`):
   - Zet `area.manual_override = True`
   - Werkt `area.target_temperature` bij naar thermostaat
   - Persisteert status via `await self.area_manager.async_save()`
   - Forceert coordinator refresh voor directe UI update

4. **Persistentie** (v0.4.1+):
   - `manual_override` flag opgeslagen in `Area.to_dict()`
   - Hersteld in `Area.from_dict()` tijdens opstarten
   - Overleeft Home Assistant herstarts

**Wissen Handmatige Override:**
- Automatisch gewist wanneer temperatuur via app API ingesteld
- API zet `area.manual_override = False` bij temperatuur wijzigingen
- Climate controller slaat zones in handmatige override modus over

**Flow:**
```
Gebruiker past thermostaat extern aan (bijv. Google Nest draaiknop)
  ↓
Status wijziging event afgevuurd door Home Assistant
  ↓
_handle_state_change() ontvangt event
  ↓
Wacht 2 seconden (debounce)
  ↓
debounced_temp_update() voert uit:
  - Zet manual_override = True
  - Werk target_temperature bij
  - Sla op naar opslag
  - Forceer coordinator refresh
  ↓
WebSocket broadcast update naar frontend
  ↓
UI toont oranje "HANDMATIG" badge (2-3 seconden vertraging)
  ↓
Climate controller slaat automatische controle over
```

### 3. Climate Controller (`climate_controller.py`)

Geautomatiseerde verwarmings controle engine met multi-apparaat ondersteuning.

**Verantwoordelijkheden:**
- Draait elke 30 seconden (via async_track_time_interval)
- Werkt zone temperaturen bij van sensoren (met F→C conversie)
- Controleert verwarming gebaseerd op hysterese logica
- Registreert temperatuur geschiedenis elke 5 minuten (10 cycli)
- Integreert met AreaManager voor effectieve doel temperatuur
- Werkt thermostaat doelen bij zelfs wanneer zone inactief is (synchroniseert met schema's)
- **Controleert alle apparaat types op gecoördineerde wijze (NIEUW)**

**Apparaat Controle Methoden:**

1. **_async_control_thermostats()** - Standaard thermostaat controle
   - Zet `climate.*` entiteiten naar doel temperatuur
   - Werkt met traditionele TRV's en slimme thermostaten

2. **_async_control_switches()** - Intelligente binaire schakelaar controle
   - Monitort thermostaat `hvac_action` attribuut om werkelijke verwarmingsstatus te detecteren
   - Houdt schakelaars AAN wanneer thermostaten actief verwarmen (zelfs wanneer zone doel bereikt)
   - Behandelt randgevallen: decimale temperatuur verschillen, thermostaat vertraging
   - Respecteert `shutdown_switches_when_idle` instelling per zone
   - Perfect voor circulatie pompen, zone kleppen, relais
   - Voorbeeld: Google Nest thermostaat verwarmt naar 19.2°C terwijl zone doel 19.2°C is → schakelaar blijft AAN tot hvac_action verandert naar "idle"

3. **_async_control_valves()** - Intelligente klep controle met dynamische capability detectie
   
   **Capability Detectie** (`_get_valve_capability()`):
   - **100% runtime detectie** - GEEN hardcoded apparaat modellen
   - Bevraagt entiteit attributen en domein om controle modus te bepalen
   - Werkt met ELKE klep van elke fabrikant (TuYa, Danfoss, Eurotronic, Sonoff, etc.)
   - Cached resultaten om herhaalde queries te vermijden
   - Retourneert:
     - `supports_position`: Boolean voor positie controle capability
     - `supports_temperature`: Boolean voor temperatuur controle capability
     - `position_min/max`: Min/max waarden voor positie entiteiten
     - `entity_domain`: Entiteit type (number, climate, etc.)
   
   **Controle Modi**:
   - **Positie modus** (`number.*` entiteiten of `climate.*` met positie attribuut):
     - Bevraagt `min`/`max` attributen van entiteit
     - Zet naar max bij verwarmen, min bij inactief
     - Voorbeeld: Elke klep met positie controle → 100% open / 0% gesloten
   - **Temperatuur modus** (fallback voor `climate.*` zonder positie):
     - Voor elke TRV die alleen temperatuur controle ondersteunt
     - Zet naar `target_temp + offset` bij verwarmen (zorgt dat klep opent)
     - Zet naar `trv_idle_temp` (standaard 10°C) bij inactief (sluit klep)
     - Voorbeeld: Zone doel 21°C → TRV gezet naar 31°C bij verwarmen, 10°C bij inactief
   - Werkt met elke externe temperatuur sensoren

4. **_async_control_opentherm_gateway()** - Globale ketel controle
   - Aggregeert verwarmings eisen over ALLE zones
   - Volgt welke zones actief verwarmen
   - Berekent maximum doel temperatuur over alle verwarmende zones
   - Ketel controle:
     - **AAN**: Wanneer zone warmte nodig heeft, setpoint = `max(area_targets) + 20°C`
     - **UIT**: Wanneer geen zones warmte nodig hebben
   - Gedeelde resource (één gateway bedient alle zones)

**Controle Flow:**
```
Elke 30 seconden:
1. Werk alle zone temperaturen bij van sensoren
2. Voor elke zone:
   - Besluit of verwarming nodig (hysterese logica)
   - Controleer thermostaten → zet doel temperatuur
   - Controleer schakelaars → aan/uit gebaseerd op verwarmings status
   - Controleer kleppen → positie of temperatuur gebaseerd op capability
   - Volg of zone verwarmt + zijn doel temp
3. Na alle zones verwerkt:
   - Aggregeer verwarmings eisen
   - Controleer OpenTherm gateway → ketel aan/uit + optimale setpoint
```

**Hysterese Logica:**
```python
# Hysterese controle (standaard 0.5°C)
should_heat = current_temp < (target_temp - hysteresis)
should_stop = current_temp >= target_temp

# Doel bevat schema's + nacht boost
target_temp = area.get_effective_target_temperature()
```

**Nacht Boost Gedrag:**

Nacht boost voegt een kleine temperatuur offset toe tijdens geconfigureerde uren om ruimtes voor te verwarmen voordat ochtend schema's activeren.

**Hoe het Werkt:**
- Werkt **additief** bovenop actieve schema's (bijv. slaap preset)
- Voorbeeld: Slaap preset (18.5°C) + Nacht boost (0.2°C) = 18.7°C tijdens boost uren
- Geconfigureerd per zone met start/eind tijden en temperatuur offset
- Meestal geconfigureerd voor 03:00-07:00 om geleidelijk op te warmen voor wektijd

**Smart Night Boost (AI-Aangedreven):**
- Gebruikt leer-engine om benodigde verwarmingstijd te voorspellen
- Vereist historische data (meerdere verwarmingscycli) voor voorspellingen
- Valt terug op reguliere nacht boost als geen leergegevens beschikbaar
- Berekent automatisch optimale starttijd gebaseerd op:
  - Huidige temperatuur
  - Doel temperatuur (van ochtend schema of geconfigureerde wektijd)
  - Voorspelde verwarmingsduur
  - Veiligheidsmarge (10 minuten)

**Prioriteits Volgorde voor Effectieve Temperatuur:**
1. Boost modus (indien actief)
2. Raam open (verlaag temperatuur)
3. Preset modus of schema temperatuur
4. Nacht boost aanpassing (+offset tijdens geconfigureerde uren)
5. Basis doel temperatuur

### 4. Schedule Executor (`scheduler.py`)

Tijd-gebaseerde temperatuur controle.

**Verantwoordelijkheden:**
- Draait elke 1 minuut (via async_track_time_interval)
- Controleert alle actieve schema's voor huidige dag/tijd
- Past temperatuur wijzigingen toe wanneer schema's activeren
- Behandelt middernacht-kruisende schema's
- Voorkomt dubbele temperatuur instellingen (volgt laatst toegepast)

**Schema Matching:**
- Dag-van-de-week controle (mon, tue, wed, thu, fri, sat, sun)
- Tijdsbereik validatie (behandelt 22:00-06:00 kruisend middernacht)
- Prioriteit: Laatste schema tijd wint

### 5. History Tracker (`history.py`)

Temperatuur logging en retentie met dubbele opslag backend ondersteuning.

**Verantwoordelijkheden:**
- Registreert temperatuur elke 5 minuten
- Slaat op: current_temp, target_temp, state, timestamp
- Configureerbare retentie: 1-365 dagen
- Dubbele opslag backends: JSON (standaard) of Database (optioneel)
- Automatische opschoning van oude entries
- 1000 entry in-memory cache per zone

**Opslag Backends:**

**JSON Opslag (Standaard):**
- Eenvoudige bestandsopslag in `.storage/smart_heating_history`
- Werkt met alle Home Assistant installaties
- Geen extra configuratie vereist
- Geschikt voor de meeste gebruikers

**Database Opslag (Optioneel - Power Users):**
- Ondersteunt MariaDB, MySQL, PostgreSQL
- Automatische detectie via Home Assistant's recorder configuratie
- Niet-blokkerende operaties via recorder's database engine
- Geoptimaliseerd schema met geïndexeerde kolommen (area_id, timestamp)
- Valt terug naar JSON voor SQLite databases (niet ondersteund)
- Vereist recorder configuratie in `configuration.yaml`:
  ```yaml
  recorder:
    db_url: mysql://user:pass@host/database
  ```

**Migratie:**
- Naadloze bidirectionele migratie tussen JSON ↔ Database
- Behoudt alle historische data tijdens migratie
- Automatische validatie voor migratie
- API endpoint: `POST /api/smart_heating/history/storage/migrate`
- Backend voorkeur blijft behouden na herstarts

**Database Validatie:**
- Draait asynchroon tijdens `async_load()`
- Laadt opgeslagen backend voorkeur uit JSON
- Valideert database beschikbaarheid via `get_instance(hass)`
- Creëert automatisch tabel als deze niet bestaat
- Valt terug naar JSON als database niet beschikbaar

**Opslag Formaat:**

JSON:
```json
{
  "storage_backend": "json",
  "retention_days": 90,
  "history": {
    "living_room": [
      {
        "timestamp": "2025-12-04T10:00:00",
        "current_temperature": 20.5,
        "target_temperature": 21.0,
        "state": "heating"
      }
    ]
  }
}
```

Database Tabel (`smart_heating_history`):
```sql
CREATE TABLE smart_heating_history (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  area_id VARCHAR(255) NOT NULL,
  timestamp DATETIME NOT NULL,
  current_temperature FLOAT NOT NULL,
  target_temperature FLOAT NOT NULL,
  state VARCHAR(50) NOT NULL,
  INDEX idx_area_timestamp (area_id, timestamp)
);
```

**API Endpoints:**
- `GET /api/smart_heating/history/config` - Haal retentie en backend instellingen op
- `POST /api/smart_heating/history/config` - Update retentie (1-365 dagen)
- `GET /api/smart_heating/history/storage/info` - Huidige backend en statistieken
- `GET /api/smart_heating/history/storage/database/stats` - Database metrieken
- `POST /api/smart_heating/history/storage/migrate` - Migreer tussen backends
- `POST /api/smart_heating/history/cleanup` - Handmatige opschoning trigger

### 6. Safety Monitor (`safety_monitor.py`)

Nooduitschakeling van verwarming bij veiligheidsalarm.

**Verantwoordelijkheden:**
- Monitort geconfigureerde veiligheidssensoren (rook, CO detectors)
- Triggert nooduitschakeling bij gedetecteerd alarm
- Schakelt alle verwarmingszones onmiddellijk uit
- Vuurt `smart_heating_safety_alert` event af
- Behoudt uitgeschakelde status (overleeft herstarts)

**Prestaties:**
- **Event-gestuurde architectuur** - Geen polling overhead
- Gebruikt `async_track_state_change_event()` voor Home Assistant event bus abonnement
- Callback wordt alleen getriggerd bij daadwerkelijke sensor statuswijzigingen
- CPU gebruik: 0% inactief, ~1-5ms per statuswijziging event
- Geheugen: Verwaarloosbaar (enkele event listener registratie)

**Configuratie:**
- Globale instelling geconfigureerd via Area Manager
- Sensor ID: Te monitoren entiteit (bijv. `binary_sensor.smoke_detector`)
- Attribuut: Specifiek attribuut om te controleren (bijv. `state`)
- Alarm waarde: Waarde die gevaar aangeeft (bijv. `on`)
- Ingeschakeld: Standaard true, kan uitgeschakeld worden voor testen

**Controle Flow:**
```
1. SafetyMonitor setup met geconfigureerde sensor
2. async_track_state_change_event registreert listener (event-gestuurd, geen polling)
3. Bij sensor status wijziging (directe notificatie van HA event bus):
   - Controleer of alarm waarde overeenkomt met geconfigureerde waarde
   - Bij match: trigger _emergency_shutdown()
     - Schakel alle zones uit via Area Manager
     - Vuur event af: smart_heating_safety_alert
     - Vraag coordinator refresh aan voor UI update
     - Log foutmelding met sensor details
4. Gebruiker moet zones handmatig herinschakelen na oplossen gevaar
   - Het herinschakelen van een zone wist de alarm status
```

**Opslag (via Area Manager):**
```json
{
  "safety_sensor_id": "binary_sensor.smoke_detector",
  "safety_sensor_attribute": "state",
  "safety_sensor_alert_value": "on",
  "safety_sensor_enabled": true
}
```

**Integratie:**
- Geconfigureerd via Globale Instellingen → Veiligheid tab in frontend
- Services: `set_safety_sensor`, `remove_safety_sensor`
- API endpoints: GET/POST/DELETE `/api/smart_heating/safety_sensor`
- WebSocket events: Real-time alarm updates via coordinator refresh

### 7. Vacation Manager (`vacation_manager.py`)

Geautomatiseerde verwarmingscontrole tijdens afwezigheid.

**Verantwoordelijkheden:**
- Beheert vakantie modus schema's met start/eind datums
- Schakelt vakantie modus automatisch in/uit op geplande tijden
- Slaat enabled status van alle zones op voordat vakantie start
- Schakelt alle zones uit tijdens vakantie (energie besparing)
- Herstelt originele zone status wanneer vakantie eindigt
- Behandelt Home Assistant herstarts tijdens vakantie periodes

**Vakantie Modus Statussen:**
- **Inactief**: Geen vakantie gepland of vakantie beëindigd
- **Actief**: Momenteel in vakantie periode (alle zones uitgeschakeld)
- **Gepland**: Vakantie geconfigureerd voor toekomstige datum

**Controle Flow:**
```
1. Gebruiker stelt vakantie datums in via Globale Instellingen → Vakantie tab
2. Vacation Manager controleert elk uur (async_track_time_interval)
3. Wanneer start tijd bereikt wordt:
   - Bewaar huidige enabled status van alle zones
   - Schakel alle zones uit
   - Stel vacation_mode_active = true in
   - Vuur event af: smart_heating_vacation_started
4. Wanneer eind tijd bereikt wordt:
   - Herstel alle zones naar originele status
   - Stel vacation_mode_active = false in
   - Vuur event af: smart_heating_vacation_ended
5. Bij HA herstart tijdens vakantie:
   - Detecteert actieve vakantie periode
   - Zones blijven uitgeschakeld (status persistent)
```

**Opslag (via Area Manager):**
```json
{
  "vacation_mode_start": "2024-12-20T15:00:00",
  "vacation_mode_end": "2024-12-27T18:00:00",
  "vacation_mode_active": true,
  "vacation_original_states": {
    "living_room": true,
    "bedroom": true,
    "bathroom": false
  }
}
```

**Integratie:**
- Geconfigureerd via Globale Instellingen → Vakantie tab in frontend
- Services: `set_vacation_mode`, `cancel_vacation_mode`
- API endpoints: GET/POST/DELETE `/api/smart_heating/vacation`
- WebSocket events: `vacation_changed`, `smart_heating_vacation_started`, `smart_heating_vacation_ended`

### 8. Platforms

#### Climate Platform (`climate.py`)
Creëert één `climate.area_<naam>` entiteit per zone.

**Kenmerken:**
- HVAC modi: HEAT, OFF
- Temperatuur controle (5-30°C, 0.5° stappen)
- Huidige zone status
- Zone attributen (apparaten, ingeschakeld)

#### Switch Platform (`switch.py`)
Creëert één `switch.area_<naam>_control` entiteit per zone.

**Kenmerken:**
- Eenvoudige aan/uit controle
- Gekoppeld aan area.enabled eigenschap

#### Sensor Platform (`sensor.py`)
Creëert `sensor.smart_heating_status` entiteit.

**Kenmerken:**
- Algemene systeem status
- Zone aantal
- Actieve zones aantal

### 9. REST API (`api.py`)

HTTP API gebruikt `HomeAssistantView` voor frontend communicatie.

**Endpoints:**

| Methode | Endpoint | Beschrijving |
|---------|----------|--------------|
| GET | `/api/smart_heating/areas` | Haal alle zones op met nacht boost data |
| GET | `/api/smart_heating/areas/{id}` | Haal specifieke zone op |
| POST | `/api/smart_heating/areas` | Creëer zone |
| DELETE | `/api/smart_heating/areas/{id}` | Verwijder zone |
| POST | `/api/smart_heating/areas/{id}/devices` | Voeg apparaat toe aan zone |
| DELETE | `/api/smart_heating/areas/{id}/devices/{device_id}` | Verwijder apparaat |
| POST | `/api/smart_heating/areas/{id}/schedules` | Voeg schema toe aan zone |
| DELETE | `/api/smart_heating/areas/{id}/schedules/{schedule_id}` | Verwijder schema |
| POST | `/api/smart_heating/areas/{id}/temperature` | Stel temperatuur in |
| POST | `/api/smart_heating/areas/{id}/enable` | Schakel zone in |
| POST | `/api/smart_heating/areas/{id}/disable` | Schakel zone uit |
| GET | `/api/smart_heating/areas/{id}/history?hours=24` | Haal temperatuur geschiedenis op |
| GET | `/api/smart_heating/devices` | Haal beschikbare apparaten op (ALLE platforms) |
| GET | `/api/smart_heating/devices/refresh` | Vernieuw apparaat ontdekking |
| GET | `/api/smart_heating/status` | Haal systeem status op |
| POST | `/api/smart_heating/call_service` | Roep HA service aan (proxy) |
| GET | `/api/smart_heating/vacation` | Haal vakantie modus configuratie op |
| POST | `/api/smart_heating/vacation` | Stel vakantie modus datums in |
| DELETE | `/api/smart_heating/vacation` | Annuleer vakantie modus |
| GET | `/api/smart_heating/safety_sensor` | Haal veiligheids sensor configuratie op |
| POST | `/api/smart_heating/safety_sensor` | Stel veiligheids sensor configuratie in |
| DELETE | `/api/smart_heating/safety_sensor` | Verwijder veiligheids sensor |

**Apparaat Ontdekking** (`GET /devices`):
- Ontdekt ALLE Home Assistant climate, sensor, switch, en number entiteiten
- Platform-onafhankelijk: Werkt met ELKE integratie (Nest, Ecobee, MQTT, Z-Wave, etc.)
- Slimme filtering:
  - Climate entiteiten: Alle climate domeinen
  - Temperatuur sensoren: device_class, unit_of_measurement, of entiteit naming
  - Schakelaars: Alleen verwarmings-gerelateerd (pompen, relais, vloerverwarming)
  - Nummers: Klep/TRV positie controles
- Retourneert apparaat metadata: entity_id, naam, type, HA zone toewijzing
- Filtert apparaten uit verborgen zones (3-methoden filtering)

### 10. WebSocket API (`websocket.py`)

Real-time communicatie gebruikt HA WebSocket API.

**Commando's:**
- `smart_heating/subscribe_updates` - Abonneer op zone updates
- `smart_heating/get_areas` - Haal zones op via WebSocket

### 11. Service Calls

Uitgebreide service API voor automatisering/script integratie:

**Zone Beheer:**
1. `smart_heating.enable_area` - Schakel zone in
2. `smart_heating.disable_area` - Schakel zone uit
3. `smart_heating.set_area_temperature` - Stel doel temperatuur in

**Apparaat Beheer:**
4. `smart_heating.add_device_to_area` - Voeg apparaat toe aan zone
5. `smart_heating.remove_device_from_area` - Verwijder apparaat

**Schema Beheer:**
6. `smart_heating.add_schedule` - Voeg tijd-gebaseerd schema toe
7. `smart_heating.remove_schedule` - Verwijder schema
8. `smart_heating.enable_schedule` - Schakel schema in
9. `smart_heating.disable_schedule` - Schakel schema uit

**Geavanceerde Instellingen:**
10. `smart_heating.set_night_boost` - Configureer nacht boost
11. `smart_heating.set_opentherm_gateway` - Configureer globale OpenTherm gateway
12. `smart_heating.set_trv_temperatures` - Stel TRV verwarmings/inactieve temperaturen in
13. `smart_heating.set_hysteresis` - Stel globale hysterese in

**Vakantie Modus:**
14. `smart_heating.set_vacation_mode` - Configureer vakantie datums
15. `smart_heating.cancel_vacation_mode` - Annuleer vakantie

**Veiligheid:**
16. `smart_heating.set_safety_sensor` - Configureer veiligheids sensor
17. `smart_heating.remove_safety_sensor` - Verwijder veiligheids sensor

**Systeem:**
18. `smart_heating.refresh` - Handmatige refresh

## Frontend Componenten

### Technology Stack

- **React 18.3** - UI library
- **TypeScript** - Type veiligheid
- **Vite 6** - Build tool en dev server
- **Material-UI (MUI) v6** - Component library
- **react-router-dom** - Client-side routing
- **react-beautiful-dnd** - Drag and drop apparaat toewijzing
- **Recharts** - Interactieve temperatuur grafieken
- **WebSocket** - Real-time updates via custom hook
- **i18next** - Internationalisatie (EN/NL)

### Component Structuur

```
src/
├── main.tsx                    # Entry point
├── App.tsx                     # Hoofd applicatie met routing
├── types.ts                    # TypeScript interfaces
├── api.ts                      # API client functies
├── i18n.ts                     # i18n configuratie
├── index.css                   # Globale styles
├── locales/
│   ├── en/translation.json     # Engelse vertalingen
│   └── nl/translation.json     # Nederlandse vertalingen
├── components/
│   ├── Header.tsx              # App header met verbindings status
│   ├── ZoneList.tsx            # Zone grid met drag-drop context
│   ├── ZoneCard.tsx            # Individuele zone controle kaart
│   ├── CreateZoneDialog.tsx    # Zone creatie dialoog
│   ├── DevicePanel.tsx         # Sleepbare apparaten sidebar
│   ├── ScheduleEditor.tsx      # Schema beheer UI
│   ├── HistoryChart.tsx        # Temperatuur geschiedenis visualisatie
│   ├── VacationModeBanner.tsx  # Vakantiemodus banner
│   └── VacationModeSettings.tsx # Vakantiemodus instellingen
├── pages/
│   ├── AreaDetail.tsx          # Gedetailleerde zone pagina (5 tabs)
│   └── GlobalSettings.tsx      # Globale instellingen pagina (5 tabs)
└── hooks/
    └── useWebSocket.ts         # WebSocket verbindings hook
```

### Belangrijkste Kenmerken

**ZoneCard Component:**
- Temperatuur slider (5-30°C, 0.5° stappen)
- In/uitschakel toggle
- Status indicator met kleurcodering (verwarmen/inactief/uit)
- Apparaten lijst met verwijder knoppen
- Drag-drop target voor apparaat toewijzing
- Klik om te navigeren naar detail pagina

**AreaDetail Pagina (5 Tabs):**
1. **Overzicht** - Temperatuur controle, huidige status, apparaat status met real-time verwarmings indicatoren
2. **Apparaten** - Verbeterd apparaat beheer met:
   - Toegewezen apparaten lijst met verwijder knoppen
   - Locatie-gebaseerde filter dropdown
   - Beschikbare apparaten met toevoeg knoppen (+/- iconen)
   - HA zone toewijzing weergegeven als chips
   - Real-time apparaat aantallen per locatie
3. **Schema** - Tijd-gebaseerde schema editor met verbeterde UI (v0.4.0):
   - Material-UI DatePicker voor kalender-gebaseerde datumselectie
   - Meerdaagse selectie met checkbox interface en snelkeuze knoppen
   - Datumspecifieke schema's voor feestdagen en speciale evenementen
   - Kaart-gebaseerde lay-out met inklapbare secties
   - Visuele schema chips met tijdsbereik en temperatuur/preset weergave
4. **Geschiedenis** - Interactieve temperatuur grafieken (6u-7d bereiken)
5. **Instellingen** - Nacht boost, hysterese, geavanceerde configuratie

**GlobalSettings Pagina (5 Tabs):**
1. **Temperatuur** - Globale temperatuur instellingen:
   - Standaard doel temperatuur
   - Minimum en maximum temperatuur limieten
   - Temperatuur stap grootte (0.5°C standaard)
2. **Sensoren** - Globale sensor configuratie:
   - Standaard sensor entiteit voor nieuwe zones
   - Sensor filtering en discovery instellingen
3. **Vakantie** - Vakantie modus beheer:
   - Start en eind datum/tijd kiezers
   - Huidige vakantie status weergave
   - Annuleer vakantie knop
   - Originele zone statussen getoond tijdens vakantie
4. **Veiligheid** - Veiligheids sensor configuratie:
   - Sensor selectie dropdown (rook/CO detectors)
   - Attribuut selectie (bijv. smoke, gas, co)
   - Alarm waarde configuratie (bijv. true, on)
   - In/uitschakelen veiligheids monitoring
   - Huidige configuratie weergave
5. **Geavanceerd** - Geavanceerde systeem instellingen:
   - Hysterese configuratie (±0.5°C standaard)
   - TRV verwarmings/inactieve temperaturen
   - OpenTherm gateway configuratie
   - Logging en debug instellingen

**Apparaat Beheer Functies:**
- **Locatie Filter Dropdown** - Filter apparaten op HA zone
  - "Alle Locaties" - Toon alle beschikbare apparaten
  - "Geen Locatie Toegewezen" - Alleen niet-toegewezen apparaten
  - Specifieke zones (Badkamer, Woonkamer, etc.) met apparaat aantallen
- **Directe Apparaat Toewijzing** - Apparaten toevoegen/verwijderen vanaf zone detail pagina
- **Toevoeg Knop** (AddCircleOutlineIcon) - Enkele klik om apparaat toe te wijzen
- **Verwijder Knop** (RemoveCircleOutlineIcon) - Enkele klik om apparaat te verwijderen
- **Locatie Chips** - Visuele indicatoren die HA zone van apparaat tonen
- **Real-time Updates** - Apparaten lijst vernieuwt na toevoeg/verwijder operaties

**ScheduleEditor Component (v0.4.0 - Verbeterde UI):**
- **Moderne Datum/Tijd Selectie:**
  - Material-UI DatePicker voor datumselectie (kalender weergave)
  - Tijd invoer voor start/eind tijden
  - Schakel tussen "Wekelijks Terugkerend" en "Specifieke Datum" schema's
- **Meerdaagse Selectie:**
  - Checkbox interface voor selecteren van meerdere dagen
  - Snelkeuze knoppen: Weekdagen, Weekend, Alle Dagen, Wissen
  - Visuele preview van geselecteerde dagen met chips
  - Teller indicator die aantal geselecteerde dagen toont
- **Kaart-Gebaseerde Lay-out:**
  - Aparte secties voor Wekelijkse en Datumspecifieke schema's
  - Inklapbare kaarten per dag (uitvouwen/inklappen voor schonere weergave)
  - Visuele iconen (🔁 Herhaal voor wekelijks, 📅 Evenement voor datumspecifiek)
  - Schema aantal badges per dag
  - Geformatteerde datums voor datumspecifieke schema's (bijv. "29 Apr, 2024")
- **Schema Types:**
  - Wekelijks Terugkerend: Creëer schema's voor meerdere dagen tegelijk
  - Datumspecifiek: Eenmalige schema's voor feestdagen, evenementen, tijdelijke wijzigingen
  - Temperatuur of Preset Modus: Schakel tussen vaste temperatuur en preset modi
- Toevoegen/verwijderen schema's met enkele klik
- Bewerk schema's door op chips te klikken
- In/uitschakelen individuele schema's
- Visuele schema chips die tijdsbereik en temperatuur/preset tonen

**HistoryChart Component:**
- Recharts lijn grafiek
- Blauwe lijn: Huidige temperatuur
- Gele streepjes: Doel temperatuur
- Rode stippen: Verwarmen actieve periodes
- Tijdsbereik selector (6u, 12u, 24u, 3d, 7d)
- Auto-refresh elke 5 minuten
- Responsief ontwerp

**DevicePanel Component:**
- **Universele Apparaat Ontdekking** - Toont ALLE Home Assistant apparaten
  - Climate entiteiten van ELKE integratie (Nest, Ecobee, MQTT, Z-Wave, etc.)
  - Temperatuur sensoren van ELK platform
  - Verwarmings-gerelateerde schakelaars (pompen, relais, vloerverwarming)
  - Klep/TRV positie controles
- Platform-onafhankelijke apparaat detectie
- Real-time beschikbaarheid updates
- Apparaat vernieuw knop voor handmatige ontdekking
- Filter op apparaat type iconen
- Toont HA zone toewijzing voor elk apparaat

**CreateZoneDialog Component:**
- Zone naam invoer
- Auto-gegenereerde area_id
- Initiële temperatuur instelling
- Formulier validatie

### API Integratie

Alle API calls gaan via `src/api.ts`:

```typescript
// Zones ophalen
const areas = await getZones()

// Zone creëren
await createZone('woonkamer', 'Woonkamer', 21.0)

// Temperatuur instellen
await setZoneTemperature('woonkamer', 22.5)

// Apparaat toevoegen
await addDeviceToZone('woonkamer', 'device_id')
```

### Real-time Updates

WebSocket verbinding voor live updates:
- Zone status wijzigingen
- Temperatuur updates
- Apparaat toevoegingen/verwijderingen
- Systeem status

## Data Flow

### Zone Creatie Flow

```
Gebruiker klikt "Zone Creëren"
    ↓
CreateZoneDialog verzamelt invoer

### Primaire Temperatuursensor Selectie (v0.5.10+)

**Functie:** Stelt gebruikers in staat te kiezen welk apparaat de temperatuur meet per zone.

**Gebruikscases:**
- Airconditioner met ingebouwde temp sensor + dedicated temperatuursensor → Gebruik dedicated sensor voor nauwkeurigheid
- Meerdere thermostaten in één zone → Kies welke thermostaat temperatuur gebruiken
- Voorkeur voor losse sensor boven AC's sensor voor consistente metingen

**Gedrag:**
```
Auto Modus (standaard):
    - primary_temperature_sensor = null
    - Middelt ALLE temperatuursensoren + thermostaten in zone
    
Primaire Sensor Modus:
    - primary_temperature_sensor = "sensor.xyz" of "climate.abc"
    - Gebruikt ALLEEN het geselecteerde apparaat voor temperatuur
    - Als geselecteerd apparaat niet beschikbaar → Valt tijdelijk terug naar auto modus
```

**Implementatie:**
- **Opslag:** `Area.primary_temperature_sensor` (str | None)
- **Temperatuur Verzameling:** `climate_handlers/temperature_sensors.py`
  - Controleert of primaire sensor is ingesteld
  - Geeft enkele temperatuur van primair apparaat terug
  - Valt terug naar middelen als primair niet beschikbaar
- **API Endpoint:** `POST /api/smart_heating/areas/{area_id}/primary_temp_sensor`
  - Valideert sensor bestaat in zone
  - Werkt temperatuur onmiddellijk bij
  - Triggert vernieuwing verwarmingscontrole
- **UI:** Zone Detail → Apparaten tab → Primaire Temperatuursensor dropdown
- **Vertalingen:** Engels + Nederlands

### Temperatuur Controle Flow

```
Gebruiker versleept temperatuur slider
    ↓
ZoneCard onChange handler
    ↓
api.setZoneTemperature() roept POST /api/.../temperature aan
    ↓
ZoneHeaterAPIView.post() routeert naar set_temperature()
    ↓
area_manager.set_area_target_temperature()
    ↓
Zone bijgewerkt in opslag
    ↓
Climate controller (30s interval) detecteert wijziging
    ↓
Climate controller verwerkt zone:
    │
    ├──→ Verzamelt temperatuur met primaire sensor (indien ingesteld) of middelen (indien null)
    │
    ├──→ Thermostaten: climate.set_temperature naar doel
    │
    ├──→ Schakelaars: switch.turn_on als verwarmen, switch.turn_off als inactief
    │
    ├──→ Kleppen:
    │    ├──→ Positie modus (number.*): Stel in op 100% als verwarmen, 0% als inactief
    │    └──→ Temperatuur modus (climate.*): Stel in op heating_temp als verwarmen, idle_temp als inactief
    │
    └──→ Volgt verwarmings status + doel voor deze zone
    ↓
Na alle zones verwerkt:
    ↓
Climate controller aggregeert eisen:
    - heating_areas = zones die momenteel warmte nodig hebben
    - max_target_temp = hoogste doel over verwarmende zones
    ↓
OpenTherm Gateway Controle:
    - Als any_heating: Ketel AAN, setpoint = max_target_temp + 20°C
    - Als geen verwarming: Ketel UIT
    ↓
Apparaten reageren (thermostaten, schakelaars, kleppen, ketel)
    ↓
Coordinator haalt bijgewerkte status op (30s interval)
    ↓
[F°→C° conversie toegepast indien nodig]
    ↓
WebSocket pusht update naar frontend
    ↓
ZoneCard toont bijgewerkte apparaat status
```

**Multi-Apparaat Coördinatie Voorbeeld:**

Woonkamer zone met doel 23°C, huidig 20°C (heeft verwarming nodig):
1. **Thermostaat** → Stel in op 23°C
2. **Pomp Schakelaar** → Schakel AAN
3. **TRV (positie modus)** → Stel in op 100% open
4. **TRV (temp modus)** → Stel in op 25°C (heating_temp)
5. Zone gevolgd als verwarmend met doel 23°C

Keuken zone met doel 19°C, huidig 21°C (geen verwarming nodig):
1. **Thermostaat** → Stel in op 19°C (blijft gesynchroniseerd)
2. **Pomp Schakelaar** → Schakel UIT
3. **TRV (positie modus)** → Stel in op 0% gesloten
4. **TRV (temp modus)** → Stel in op 10°C (idle_temp)
5. Zone gevolgd als inactief

OpenTherm Gateway (globaal):
- Woonkamer heeft warmte nodig (doel 23°C), Keuken niet
- Ketel AAN, setpoint = 23 + 20 = 43°C

**Opmerking over Mock Apparaten:**
Met mock MQTT apparaten reageren klep posities niet op commando's omdat er geen fysieke hardware is. Echte TRV's zouden automatisch hun klep positie aanpassen op basis van temperatuur commando's en terugrapporteren via MQTT.

## Opslag

Zones en configuratie worden opgeslagen met Home Assistant's storage API:

**Bestand:** `.storage/smart_heating_areas`

**Formaat:**
```json
{
  "version": 1,
  "data": {
    "areas": [
      {
        "id": "woonkamer",
        "name": "Woonkamer",
        "target_temperature": 21.0,
        "enabled": true,
        "devices": [
          {
            "id": "device_1",
            "name": "Woonkamer Thermostaat",
            "type": "thermostat"
          }
        ]
      }
    ]
  }
}
```

## Code Structuur

**v0.6.0+ Modulaire Architectuur:**

De backend is gerefactored naar een schone modulaire structuur volgens single-responsibility principes:

### Core Integratie Bestanden
- `__init__.py` (591 regels) - Integratie setup, coordinator initialisatie
- `area_manager.py` - Zone beheer en opslag
- `coordinator.py` - Data update coordinator met manual override detectie
- `climate.py` - Climate platform (zone entiteiten)
- `switch.py` - Switch platform (zone in/uitschakelen)
- `sensor.py` - Sensor platform
- `config_flow.py` - Configuratie flow

### Service Handler Modules (`ha_services/`)
Geëxtraheerd uit `__init__.py` - 29 Home Assistant service handlers:
- `__init__.py` - Centrale exports
- `schemas.py` - 22 service validatie schemas
- `area_handlers.py` - Stel temperatuur in, in/uitschakelen zone
- `device_handlers.py` - Apparaten toevoegen/verwijderen
- `schedule_handlers.py` - Schema beheer, nacht boost, kopiëren
- `hvac_handlers.py` - Preset modus, boost modus, HVAC modus
- `sensor_handlers.py` - Raam/aanwezigheid sensor beheer
- `config_handlers.py` - Globale instellingen, vorst bescherming, presets
- `safety_handlers.py` - Veiligheidssensor configuratie
- `vacation_handlers.py` - Vakantie modus controle
- `system_handlers.py` - Refresh, status

### API Handler Modules (`api_handlers/`)
Geëxtraheerd uit `api.py` - 60+ REST API endpoint handlers:
- `__init__.py` - Centrale exports
- `areas.py` - 12 zone beheer endpoints
- `devices.py` - 4 apparaat ontdekking/toewijzing endpoints
- `schedules.py` - 5 schema/preset/boost endpoints
- `sensors.py` - 5 sensor beheer endpoints
- `config.py` - 15 globale configuratie endpoints
- `history.py` - 4 geschiedenis/leer endpoints
- `logs.py` - 1 logging endpoint
- `system.py` - 3 systeem status endpoints
- `users.py` - **6 gebruikersbeheer endpoints (v0.6.0+)**
- `efficiency.py` - **3 efficiëntie rapportage endpoints (v0.6.0+)**
- `comparison.py` - **2 historische vergelijking endpoints (v0.6.0+)**

### Manager/Controller Modules
- `climate_controller.py` - HVAC apparaat controle logica
- `scheduler.py` - Schema uitvoering (1-minuut interval)
- `learning_engine.py` - ML-gebaseerd temperatuur leren
- `safety_monitor.py` - Nooduitschakeling bij veiligheidsalarm
- `vacation_manager.py` - Vakantie modus coördinatie
- `history.py` - Temperatuur logging en retentie
- `area_logger.py` - Per-zone gebeurtenis logging
- `user_manager.py` - **Multi-gebruiker aanwezigheid tracking (v0.6.0+)**
- `efficiency_calculator.py` - **Verwarmingsefficiëntie analyses (v0.6.0+)**
- `comparison_engine.py` - **Historische prestatie vergelijkingen (v0.6.0+)**

### Model Modules (`models/`)
- `area.py` - Zone data model
- `schedule.py` - Schema data model

### Utility Modules (`utils/`)
- `validators.py` - Input validatie functies
- `response_builders.py` - API response formatting
- `coordinator_helpers.py` - Coordinator utility functies
- `device_registry.py` - HA device registry helpers

### API & Communicatie
- `api.py` (446 regels) - REST API routing, statische bestand serving
- `websocket.py` - WebSocket real-time updates

**Refactoring Impact:**
- Fase 2 (ha_services/): `__init__.py` gereduceerd van 1,126 → 591 regels (47% reductie)
- Fase 3 (api_handlers/): `api.py` gereduceerd van 2,518 → 446 regels (82% reductie)
- Totaal: 72% code reductie met 20 gefocuste, single-responsibility modules
- Onderhoudbaarheid: Significant verbeterd met duidelijke scheiding van verantwoordelijkheden

## Zigbee2MQTT Integratie

### Apparaat Ontdekking

Apparaten worden ontdekt via MQTT topics:
- `zigbee2mqtt/bridge/devices` - Lijst van alle apparaten
- `zigbee2mqtt/<friendly_name>` - Apparaat status

### Apparaat Controle

Controle berichten verzonden naar:
- `zigbee2mqtt/<friendly_name>/set` - Verzend commando's

Voorbeeld:
```json
{
  "temperature": 22.5,
  "system_mode": "heat"
}
```

## Beveiliging

- **Authenticatie**: Alle API endpoints vereisen HA authenticatie
- **Autorisatie**: Gebruikt HA's ingebouwde gebruikers permissies
- **CORS**: Geconfigureerd voor same-origin alleen
- **Input Validatie**: Alle inputs gevalideerd voor verwerking

## Prestaties

- **Coordinator Poll**: 30-seconden interval (configureerbaar)
- **API Response Tijd**: < 100ms voor typische operaties
- **Frontend Bundle**: ~500KB gzipped
- **WebSocket**: Minimale overhead voor real-time updates

## Uitbreidbaarheid

### Nieuwe Apparaat Types Toevoegen

1. Voeg apparaat type constante toe in `const.py`
2. Werk apparaat afhandeling bij in `area_manager.py`
3. Voeg icoon toe in `DevicePanel.tsx`

### Nieuwe Platforms Toevoegen

1. Creëer platform bestand (bijv. `number.py`)
2. Voeg toe aan `PLATFORMS` in `const.py`
3. Forward setup in `__init__.py`

### Nieuwe API Endpoints Toevoegen

1. Voeg methode toe aan `ZoneHeaterAPIView` in `api.py`
2. Voeg client functie toe aan `frontend/src/api.ts`
3. Gebruik in React componenten

## V0.6.0 Functies: Analyses & Multi-Gebruiker Systeem

### Multi-Gebruiker Aanwezigheid Tracking (`user_manager.py`)

Beheert meerdere gebruikers met individuele verwarmingsvoorkeuren en aanwezigheidsdetectie.

**Kernfunctionaliteit:**
- **Gebruikersbeheer**: Maak, werk bij, verwijder gebruikers gekoppeld aan Home Assistant persoon entiteiten
- **Aanwezigheidsdetectie**: Volgt automatisch wie thuis is via persoon entiteit statussen
- **Voorkeur Samenvoegen**: Combineert meerdere gebruikers preset voorkeuren wanneer meerdere mensen thuis zijn
- **Prioriteit Systeem**: Gebruiker met hoogste prioriteit heeft voorrang bij conflicten
- **Zone-Specifieke Gebruikers**: Optionele zone beperkingen voor per-kamer gebruikersvoorkeuren

**Data Model:**
```python
User:
  - user_id: str (persoon entiteit ID, bijv. "person.john")
  - name: str (weergave naam)
  - preset_preferences: Dict[str, float] (home: 21.0, away: 16.0, etc.)
  - priority: int (1-10, hoger = meer prioriteit)
  - areas: List[str] (optionele zone beperkingen)

PresenceState:
  - users_home: List[str] (momenteel aanwezige gebruiker IDs)
  - active_user: Optional[str] (hoogste prioriteit gebruiker)
  - combined_mode: str ("none", "single", "multiple")

Settings:
  - multi_user_strategy: str ("priority" of "average")
  - enabled: bool
```

**Samenvoeg Strategieën:**
1. **Prioriteit Modus** (standaard): Voorkeuren van gebruiker met hoogste prioriteit winnen
2. **Gemiddelde Modus**: Gemiddelde temperatuur over alle aanwezige gebruikers

**API Endpoints:**
- `GET /api/smart_heating/users` - Lijst alle gebruikers met aanwezigheid status
- `POST /api/smart_heating/users` - Maak nieuwe gebruiker
- `PUT /api/smart_heating/users/{user_id}` - Werk gebruikersvoorkeuren bij
- `DELETE /api/smart_heating/users/{user_id}` - Verwijder gebruiker
- `PUT /api/smart_heating/users/settings` - Werk globale instellingen bij

**Integratie:**
- Wordt automatisch bijgewerkt wanneer persoon entiteiten van status veranderen (thuis/weg)
- Preset temperaturen passen aan op basis van actieve gebruiker(s)
- Opgeslagen in Home Assistant storage
- Real-time WebSocket updates naar frontend

### Efficiëntie Calculator (`efficiency_calculator.py`)

Analyseert verwarmingssysteem prestaties met behulp van historische climate entiteit data.

**Berekende Metrieken:**
- **Energie Score** (0-100): Algemene efficiëntie rating
  - Factoren: verwarmingstijd, temperatuur delta, cyclus frequentie, stabiliteit
  - Hogere score = efficiëntere werking
- **Verwarmingstijd Percentage**: % van tijd dat HVAC actief verwarmde
- **Gemiddelde Temperatuur Delta**: Gemiddeld verschil tussen doel en werkelijke temperatuur
- **Verwarmingscycli**: Aantal aan/uit cycli (minder = betere efficiëntie)
- **Temperatuur Stabiliteit**: Standaarddeviatie van temperatuur variaties

**Ondersteunde Tijdsperiodes:**
- `day` - Laatste 24 uur
- `week` - Laatste 7 dagen
- `month` - Laatste 30 dagen
- `custom` - Gebruiker-gedefinieerde datumbereik

**Data Bron:**
- Gebruikt Home Assistant recorder database via `history.state_changes_during_period()`
- Analyseert climate entiteit statussen (hvac_action, current_temperature, temperature attributen)
- Voert queries uit in recorder executor voor optimale prestaties

**Aanbevelingen Engine:**
Genereert bruikbare inzichten gebaseerd op metrieken:
- "Uitstekende efficiëntie" (score > 80)
- "Goede isolatie gedetecteerd" (lage delta)
- "Verlaag doeltemperatuur" (hoge verwarmingstijd)
- "Controleer op tocht" (hoge cyclus)
- "Verbeter isolatie" (slechte stabiliteit)

**API Endpoints:**
- `GET /api/smart_heating/efficiency/all_areas?period=week` - Samenvatting voor alle zones
- `GET /api/smart_heating/efficiency/report/{area_id}?period=week` - Enkele zone efficiëntie
- `GET /api/smart_heating/efficiency/history/{area_id}?period=week` - Multi-dag uitsplitsing

**Retour Structuur:**
```json
{
  "area_id": "woonkamer",
  "period": "week",
  "start_time": "2025-12-02T00:00:00",
  "end_time": "2025-12-09T00:00:00",
  "heating_time_percentage": 35.2,
  "average_temperature_delta": 0.8,
  "heating_cycles": 12,
  "energy_score": 78.5,
  "temperature_stability": 0.4,
  "data_points": 8640,
  "recommendations": [
    "Goede efficiëntie - behoud huidige instellingen"
  ]
}
```

### Vergelijkings Engine (`comparison_engine.py`)

Vergelijkt verwarmingsprestaties over verschillende tijdsperiodes om verbeteringen te volgen.

**Vergelijkings Types:**
1. **Week-over-Week**: Huidige week vs vorige week
2. **Maand-over-Maand**: Huidige maand vs vorige maand
3. **Aangepaste Periodes**: Gebruiker-gedefinieerde datumbereiken

**Delta Berekeningen:**
Voor elke metriek, berekent:
- **Absolute Verandering**: Huidig - Vorig
- **Percentage Verandering**: ((Huidig - Vorig) / Vorig) × 100
- **Verbeterings Vlag**: Boolean die aangeeft of verandering gunstig is
- **Energie Besparing Schatting**: Geprojecteerde energie reductie percentage

**Verbeteringslogica:**
- Energie Score: Hoger is beter
- Verwarmingstijd: Lager is beter (minder energie gebruikt)
- Temperatuur Delta: Lager is beter (dichter bij doel)
- Verwarmingscycli: Lager is beter (stabieler)
- Temperatuur Stabiliteit: Lager is beter (minder fluctuatie)

**Samenvatting Generatie:**
Genereert automatisch leesbare samenvattingen:
- "Efficiëntie verbeterd met 12.5% - geweldige vooruitgang!"
- "Efficiëntie gedaald met 5.2% - waarschijnlijk door weersveranderingen"
- "Kleine efficiëntie daling van 1.8% - binnen normale variatie"

**API Endpoints:**
- `GET /api/smart_heating/comparison/{period}` - Week/maand vergelijking voor alle zones
- `POST /api/smart_heating/comparison/custom` - Aangepaste datumbereik vergelijking

**Aangepaste Vergelijking Verzoek:**
```json
{
  "area_id": "woonkamer",
  "start_a": "2025-12-01T00:00:00",
  "end_a": "2025-12-07T00:00:00",
  "start_b": "2025-11-24T00:00:00",
  "end_b": "2025-11-30T00:00:00"
}
```

**Retour Structuur:**
```json
{
  "area_id": "woonkamer",
  "comparison_type": "week",
  "period_a": {
    "name": "Huidige Periode",
    "start": "2025-12-02T00:00:00",
    "end": "2025-12-09T00:00:00",
    "metrics": { /* volledige efficiëntie metrieken */ }
  },
  "period_b": {
    "name": "Laatste 1 we(e)k(en)",
    "start": "2025-11-25T00:00:00",
    "end": "2025-12-02T00:00:00",
    "metrics": { /* volledige efficiëntie metrieken */ }
  },
  "delta": {
    "energy_score": {
      "absolute": 5.2,
      "percentage": 7.1,
      "current": 78.5,
      "previous": 73.3,
      "improved": true
    },
    "estimated_energy_savings": {
      "percentage": 7.1,
      "description": "Energieverbruik significant gedaald."
    }
  },
  "summary": "Efficiëntie verbeterd met 7.1% - geweldige vooruitgang!"
}
```

**Integratie met Frontend:**
- Drie nieuwe React componenten: `UserManagement`, `EfficiencyReports`, `HistoricalComparisons`
- Real-time updates via WebSocket subscriptions
- Material-UI grafieken en delta indicatoren (▲/▼ pijlen met kleur codering)
- Periode selectoren voor dag/week/maand weergaven
- Aangepaste datumbereik kiezers voor flexibele analyse

**Prestatie Overwegingen:**
- Database queries gebruiken recorder executor (non-blocking)
- Resultaten gesorteerd voor UX (slechtste efficiëntie eerst voor rapporten, beste verbeteringen eerst voor vergelijkingen)
- Lege data netjes afgehandeld met "Geen data beschikbaar" berichten
- Caching mogelijkheden voor veelgebruikte periodes (toekomstige verbetering)

## Toekomstige Verbeteringen

- [x] ~~Multi-gebruiker aanwezigheid tracking~~ **Geïmplementeerd in v0.6.0**
- [x] ~~Analytics dashboard~~ **Geïmplementeerd in v0.6.0**
- [ ] Drag-and-drop apparaat toewijzing
- [ ] Slimme verwarmings algoritmes met ML voorspellingen
- [ ] Energie monitoring integratie met utility meters
- [ ] Exporteer analyses rapporten naar PDF/CSV
- [ ] Mobiele app integratie
- [ ] Spraakbesturing optimalisatie
- [ ] Weer-gebaseerde efficiëntie correcties
- [ ] Kosten analyse met energie prijzen
