# Architectuur Overzicht

Smart Heating is een Home Assistant integratie met een moderne web-gebaseerde interface voor het beheren van multi-zone verwarmingssystemen.

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
│  │  │                                                │    │ │
│  │  │        REST API + WebSocket API                │    │ │
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
  - day: str (Monday, Tuesday, etc.) [nieuw formaat]
  - start_time: str (HH:MM) [nieuw formaat]
  - end_time: str (HH:MM) [nieuw formaat]
  - temperature: float
  - days: List[str] (mon, tue, etc.) [legacy]
  - enabled: bool

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

2. **_async_control_switches()** - Binaire schakelaar controle
   - Schakelt `switch.*` entiteiten AAN wanneer zone verwarmt
   - Schakelt UIT wanneer zone inactief
   - Perfect voor circulatie pompen, zone kleppen, relais

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

Temperatuur logging en retentie.

**Verantwoordelijkheden:**
- Registreert temperatuur elke 5 minuten
- Slaat op: current_temp, target_temp, state, timestamp
- 7-dagen automatische retentie
- Persistente opslag in `.storage/smart_heating_history`
- Automatische opschoning van oude entries
- 1000 entry limiet per zone

**Opslag:**
```json
{
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
│   └── AreaDetail.tsx          # Gedetailleerde zone pagina (7 tabs)
└── hooks/
    └── useWebSocket.ts         # WebSocket verbindings hook
```

*Voor volledige component details en data flows, zie de Engelse versie van dit document in `docs/en/ARCHITECTURE.md`*

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

## Beveiliging

- **Authenticatie**: Alle API endpoints vereisen HA authenticatie
- **Autorisatie**: Gebruikt HA's ingebouwde gebruikers permissies
- **CORS**: Geconfigureerd voor same-origin alleen
- **Input Validatie**: Alle inputs gevalideerd voor verwerking

## Prestaties

- **Coordinator Poll**: 30-seconden interval (configureerbaar)
- **API Response Tijd**: < 100ms voor typische operaties
- **Frontend Bundle**: ~1.4MB (421KB gzipped)
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

---

**Opmerking**: Dit is een verkorte Nederlandse versie. Voor volledige technische details, API endpoints, en code voorbeelden, raadpleeg de Engelse versie in `docs/en/ARCHITECTURE.md`.
