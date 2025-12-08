# Ontwikkelaar Snelle Referentie

Snelle referentie voor het ontwikkelen en uitbreiden van Smart Heating.

## 🔄 Huidige Versie & Roadmap

**Huidige Stabiel**: v0.6.0
**Volgende Release**: v0.7.0 (Planningsfase)

### v0.6.0 Release (UITGEBRACHT)

**Uitgebrachte Functies**:
1. ✅ **Vakantiemodus** - Eén-klik weg modus voor alle zones
2. ✅ **Internationalisatie (i18n)** - Meertalige ondersteuning (Engels/Nederlands)

**Geplande Functies voor v0.7.0**:
3. **Import/Export** - Configuratie backup en herstel
4. **Multi-Gebruiker Aanwezigheid** - Per-gebruiker temperatuur voorkeuren
5. **Efficiëntie Rapporten** - Verwarmings prestatie analytics
6. **Historische Vergelijkingen** - Tijd-periode vergelijkingen

**Implementatie Strategie**: Incrementele releases met volledige testing bij elke fase.

---

## Project Structuur

```
smart_heating/
├── custom_components/smart_heating/
│   ├── __init__.py           # Integratie setup, service registratie
│   ├── manifest.json         # Integratie metadata
│   ├── const.py              # Constanten en configuratie
│   ├── config_flow.py        # Config flow (lege init)
│   ├── strings.json          # UI strings
│   ├── services.yaml         # Service definities
│   │
│   ├── area_manager.py       # Kern zone beheer logica
│   ├── coordinator.py        # Data update coordinator
│   ├── api.py                # REST API endpoints
│   ├── websocket.py          # WebSocket handlers
│   │
│   ├── climate_controller.py # Verwarmings controle logica
│   ├── scheduler.py          # Schema beheer
│   ├── learning_engine.py    # Adaptief leer systeem
│   ├── history.py            # Temperatuur geschiedenis tracking
│   ├── area_logger.py        # Ontwikkelings logging systeem
│   │
│   ├── vacation_manager.py   # Vakantiemodus (v0.6.0)
│   │
│   ├── climate.py            # Climate platform
│   ├── switch.py             # Switch platform
│   ├── sensor.py             # Sensor platform
│   │
│   └── frontend/             # React frontend
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── index.html
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── types.ts
│           ├── api.ts
│           ├── i18n.ts       # i18n configuratie (v0.6.0)
│           ├── locales/      # Vertalingen (v0.6.0)
│           │   ├── en/translation.json
│           │   └── nl/translation.json
│           └── components/
│               ├── Dashboard.tsx
│               ├── GlobalSettings.tsx
│               ├── VacationModeSettings.tsx  # v0.6.0
│               └── AreaDetail.tsx
│
├── docs/                     # Meertalige documentatie (v0.6.0)
│   ├── README.md
│   ├── en/                   # Engelse documentatie
│   │   ├── ARCHITECTURE.md
│   │   └── DEVELOPER.md
│   └── nl/                   # Nederlandse documentatie
│       ├── ARCHITECTURE.md
│       └── DEVELOPER.md
│
├── README.md                 # Gebruikers documentatie (Engels)
├── README.nl.md              # Gebruikers documentatie (Nederlands)
├── CHANGELOG.md              # Versie geschiedenis (Engels)
├── CHANGELOG.nl.md           # Versie geschiedenis (Nederlands)
├── ARCHITECTURE.md           # Architectuur overzicht (Engels, root)
├── DEVELOPER.md              # Ontwikkelaar referentie (Engels, root)
├── V0.6.0_ARCHITECTURE.md    # v0.6.0 technisch ontwerp
├── V0.6.0_ROADMAP.md         # v0.6.0 implementatie plan
├── deploy_production.sh      # Productie deploy script
├── sync.sh                   # Ontwikkelings sync script
├── setup.sh                  # Test omgeving setup
└── .gitignore                # Git ignore regels
```

## E2E Testing

Smart Heating bevat uitgebreide end-to-end tests met Playwright:

```bash
cd tests/e2e
npm test                    # Voer alle tests uit
npm test -- --headed        # Voer uit met browser zichtbaar
npm test -- --debug         # Voer uit in debug mode
```

**Test Bestanden:**
- `navigation.spec.ts` - Navigatie en UI tests
- `temperature-control.spec.ts` - Temperatuur aanpassing tests
- `boost-mode.spec.ts` - Boost mode functionaliteit
- `manual-override.spec.ts` - Handmatige override detectie (5 tests)
- `switch-shutdown-control.spec.ts` - Schakelaar/pomp controle (6 tests)
- `comprehensive-features.spec.ts` - Volledige functie dekking
- `sensor-management.spec.ts` - Sensor integratie tests
- `backend-logging.spec.ts` - Backend logging verificatie
- `vacation-mode.spec.ts` - Vakantiemodus tests (9 tests, v0.6.0)

**Test Dekking:**
- 109 totale tests
- 105 geslaagde tests
- 4 overgeslagen tests (preset-modes, sensors)

## Veelvoorkomende Taken

### Een Nieuwe Service Toevoegen

1. **Definieer constante** in `const.py`:
   ```python
   SERVICE_MY_NEW_SERVICE = "my_new_service"
   ```

2. **Voeg schema toe** in `__init__.py`:
   ```python
   MY_SERVICE_SCHEMA = vol.Schema({
       vol.Required("param"): cv.string,
   })
   ```

3. **Creëer handler** in `async_setup_services()`:
   ```python
   async def handle_my_service(call: ServiceCall) -> None:
       param = call.data["param"]
       # Doe iets
       await coordinator.async_refresh()
   ```

4. **Registreer service**:
   ```python
   hass.services.async_register(
       DOMAIN, SERVICE_MY_NEW_SERVICE, handle_my_service, schema=MY_SERVICE_SCHEMA
   )
   ```

5. **Documenteer** in `services.yaml`:
   ```yaml
   my_new_service:
     description: "Omschrijving van service"
     fields:
       param:
         description: "Parameter omschrijving"
         example: "voorbeeld_waarde"
   ```

### Frontend Ontwikkeling

**Development Server Starten:**
```bash
cd smart_heating/frontend
npm install
npm run dev
```

**Productie Build:**
```bash
npm run build
```

**Testen:**
```bash
npm run lint
npm run type-check
```

### i18n Vertalingen Toevoegen (v0.6.0+)

**Nieuwe Vertaling Sleutel Toevoegen:**

1. **Voeg toe aan Engels** (`src/locales/en/translation.json`):
   ```json
   {
     "common": {
       "myNewKey": "My New Text"
     }
   }
   ```

2. **Voeg toe aan Nederlands** (`src/locales/nl/translation.json`):
   ```json
   {
     "common": {
       "myNewKey": "Mijn Nieuwe Tekst"
     }
   }
   ```

3. **Gebruik in Component**:
   ```typescript
   import { useTranslation } from 'react-i18next'
   
   const MyComponent = () => {
     const { t } = useTranslation()
     return <div>{t('common.myNewKey')}</div>
   }
   ```

**Nieuwe Taal Toevoegen:**

1. Creëer vertaal bestand: `src/locales/{lang}/translation.json`
2. Kopieer van `en/translation.json` en vertaal alle sleutels
3. Werk `i18n.ts` resources bij:
   ```typescript
   const resources = {
     en: { translation: translationEN },
     nl: { translation: translationNL },
     de: { translation: translationDE } // nieuwe taal
   }
   ```
4. Voeg toe aan ondersteunde talen: `supportedLngs: ['en', 'nl', 'de']`
5. Update Header taal menu
6. Creëer documentatie in `docs/{lang}/`

### Deployment

**Naar Test Omgeving:**
```bash
./sync.sh
```

**Naar Productie:**
```bash
./deploy_production.sh
```

## API Ontwikkeling

### REST API Endpoint Toevoegen

**Voorbeeld: Primaire Temperatuursensor (v0.5.10)**

Deze functie demonstreert de volledige stack voor het toevoegen van een nieuw API endpoint.

1. **Backend Handler** (`api_handlers/area_handlers.py`):
   ```python
   async def handle_set_primary_temperature_sensor(
       request: web.Request,
       area_manager: AreaManager,
       area_id: str
   ) -> web.Response:
       """Stel primaire temperatuursensor in voor zone."""
       data = await request.json()
       sensor_id = data.get("sensor_id")
       
       # Valideer zone bestaat
       area = await area_manager.get_area(area_id)
       if not area:
           return web.json_response({"error": "Zone niet gevonden"}, status=404)
       
       # Valideer sensor (kan null zijn voor auto modus)
       if sensor_id:
           devices = area.get_all_devices()
           if sensor_id not in devices:
               return web.json_response(
                   {"error": "Sensor niet gevonden in zone"}, 
                   status=400
               )
       
       # Werk zone bij
       area.primary_temperature_sensor = sensor_id
       await area_manager.update_area(area)
       
       return web.json_response({"success": True, "sensor_id": sensor_id})
   ```

2. **Route Registratie** (`api.py`):
   ```python
   # In ZoneHeaterAPIView.post()
   if len(parts) == 3 and parts[2] == "primary_temp_sensor":
       return await handle_set_primary_temperature_sensor(
           request, self.area_manager, parts[1]
       )
   ```

3. **Frontend API Client** (`frontend/src/api.ts`):
   ```typescript
   export const setPrimaryTemperatureSensor = async (
     areaId: string,
     sensorId: string | null
   ): Promise<void> => {
     await client.post(`/areas/${areaId}/primary_temp_sensor`, {
       sensor_id: sensorId,
     })
   }
   ```

4. **React Component** (`AreaDetail.tsx`):
   ```typescript
   import { setPrimaryTemperatureSensor } from '../api'
   
   const handlePrimarySensorChange = async (event: SelectChangeEvent) => {
     const value = event.target.value === 'auto' ? null : event.target.value
     await setPrimaryTemperatureSensor(area.id, value)
     // Vernieuw zone data
     await fetchAreaData()
   }
   ```

5. **Temperatuur Verzameling Logica** (`climate_handlers/temperature_sensors.py`):
   ```python
   async def collect_area_temperatures(
       hass: HomeAssistant,
       area: Area
   ) -> dict[str, float]:
       """Verzamel temperaturen, prioriteer primaire sensor indien ingesteld."""
       
       # Als primaire sensor geconfigureerd, gebruik deze exclusief
       if area.primary_temperature_sensor:
           state = hass.states.get(area.primary_temperature_sensor)
           if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
               temp = float(state.state)
               return {area.primary_temperature_sensor: temp}
       
       # Val terug naar middelen van alle sensoren
       temps = {}
       for sensor_id in area.temperature_sensors:
           state = hass.states.get(sensor_id)
           if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
               temps[sensor_id] = float(state.state)
       return temps
   ```

### REST API Endpoint Toevoegen (Algemeen)

1. **Voeg methode toe** aan `ZoneHeaterAPIView` in `api.py`:
   ```python
   async def my_endpoint(self, request: web.Request) -> web.Response:
       """Behandel mijn endpoint."""
       data = await request.json()
       result = await self.area_manager.do_something(data)
       return self.json(result)
   ```

2. **Voeg route toe** in `post()` of `get()`:
   ```python
   if len(parts) == 2 and parts[1] == "my_endpoint":
       return await self.my_endpoint(request)
   ```

3. **Voeg client functie toe** in `frontend/src/api.ts`:
   ```typescript
   export const myEndpoint = async (data: MyData): Promise<Result> => {
     const response = await client.post('/my_endpoint', data)
     return response.data
   }
   ```

4. **Gebruik in component**:
   ```typescript
   import { myEndpoint } from '../api'
   
   const handleAction = async () => {
     await myEndpoint({ param: 'value' })
   }
   ```
   ```python
   async def get_my_endpoint(self, request: web.Request) -> web.Response:
       """Haal mijn data op."""
       data = {"result": "success"}
       return self.json(data)
   ```

2. **Registreer route** in `async_setup()`:
   ```python
   hass.http.register_view(ZoneHeaterAPIView())
   ```

3. **Voeg client functie toe** in `frontend/src/api.ts`:
   ```typescript
   export async function getMyData(): Promise<MyDataType> {
     const response = await fetch('/api/smart_heating/my_endpoint')
     return response.json()
   }
   ```

4. **Gebruik in React**:
   ```typescript
   const data = await getMyData()
   ```

## Debugging

### Backend Logs

**Schakel debug logging in** in Home Assistant `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.smart_heating: debug
```

**Bekijk logs:**
```bash
# Docker
docker logs -f homeassistant-test

# Terminal
tail -f /config/home-assistant.log
```

### Frontend Debugging

**Browser Console:**
- Open Developer Tools (F12)
- Check Console tab voor errors
- Check Network tab voor API calls

**React DevTools:**
- Installeer React Developer Tools browser extensie
- Inspecteer component state en props

### WebSocket Debugging

**Monitor WebSocket berichten:**
```typescript
// In useWebSocket.ts
console.log('WebSocket message:', message)
```

**Forceer reconnect:**
```typescript
wsRef.current?.close()
```

## Versie Beheer

### Changelog Bijwerken

**Bij elke wijziging, update BEIDE taalversies:**

1. **Engels** (`CHANGELOG.md`):
   ```markdown
   ## [0.x.0] - 2025-XX-XX
   
   ### Added
   - New feature description
   ```

2. **Nederlands** (`CHANGELOG.nl.md`):
   ```markdown
   ## [0.x.0] - 2025-XX-XX
   
   ### Toegevoegd
   - Nieuwe functie omschrijving
   ```

### Architectuur Documentatie Bijwerken

**Bij architectuur wijzigingen, update BEIDE:**

1. `docs/en/ARCHITECTURE.md` (Engels)
2. `docs/nl/ARCHITECTURE.md` (Nederlands)

Optioneel: Update ook root `ARCHITECTURE.md` (Engels) voor snelle toegang.

### Release Process

1. **Update versie nummers:**
   - `manifest.json` - version field
   - `package.json` - version field
   - `CHANGELOG.md` / `CHANGELOG.nl.md` - nieuwe sectie

2. **Update documentatie:**
   - `README.md` / `README.nl.md` - nieuwe functies
   - `ARCHITECTURE.md` / `docs/en/ARCHITECTURE.md` / `docs/nl/ARCHITECTURE.md`
   - `DEVELOPER.md` / `docs/en/DEVELOPER.md` / `docs/nl/DEVELOPER.md`

3. **Run tests:**
   ```bash
   cd tests/e2e
   npm test
   ```

4. **Build frontend:**
   ```bash
   cd smart_heating/frontend
   npm run build
   ```

5. **Commit en tag:**
   ```bash
   git add .
   git commit -m "Release v0.x.0: Feature description"
   git tag v0.x.0
   git push origin main --tags
   ```

## Best Practices

### Code Stijl

**Python:**
- Volg PEP 8
- Gebruik type hints
- Async/await voor I/O operaties
- Docstrings voor publieke functies

**TypeScript/React:**
- Gebruik TypeScript strict mode
- Functional components met hooks
- Props interfaces voor alle components
- Gebruik `useTranslation` voor alle UI tekst

### Testing

**Backend:**
- Test alle service handlers
- Test API endpoints
- Mock externe dependencies

**Frontend:**
- E2E tests voor kritieke flows
- Test beide talen (EN/NL)
- Test op verschillende schermformaten

### Testen Veiligheids Sensor Functie

De test omgeving (setup.sh) bevat twee veiligheids sensoren voor testen:

**Test Sensoren:**
- `binary_sensor.smoke_detector` - MOES TS0205 rookmelder
- `binary_sensor.co_detector` - TuYa TS0222 CO detector

**Testen Nooduitschakeling:**

1. **Configureer Veiligheids Sensor:**
   - Navigeer naar Globale Instellingen → Veiligheid tab
   - Selecteer sensor: `binary_sensor.smoke_detector`
   - Stel attribuut in: `smoke`
   - Stel alarm waarde in: `true`
   - Schakel monitoring in

2. **Trigger Nooduitschakeling:**
   ```bash
   # Simuleer rookalarm via MQTT
   mosquitto_pub -h localhost -p 1883 \
     -t zigbee2mqtt/smoke_detector \
     -m '{"smoke": true, "battery": 100, "linkquality": 120}'
   ```

3. **Verifieer Gedrag:**
   - Alle zones moeten onmiddellijk uitgeschakeld worden
   - Persistente notificatie moet verschijnen in Home Assistant
   - Check logs: `docker logs -f homeassistant-test | grep "SAFETY ALERT"`
   - Verifieer event afgevuurd: `smart_heating_safety_alert`

4. **Wis Alarm en Herinschakelen:**
   ```bash
   # Wis rookalarm
   mosquitto_pub -h localhost -p 1883 \
     -t zigbee2mqtt/smoke_detector \
     -m '{"smoke": false, "battery": 100, "linkquality": 120}'
   
   # Schakel zones handmatig weer in via UI of API
   curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8123/api/smart_heating/areas/AREA_ID/enable
   ```

5. **Test Persistentie:**
   - Trigger nooduitschakeling
   - Herstart Home Assistant: `docker restart homeassistant-test`
   - Verifieer zones blijven uitgeschakeld na herstart

**Testen CO Detector:**
```bash
# Trigger CO alarm
mosquitto_pub -h localhost -p 1883 \
  -t zigbee2mqtt/co_detector \
  -m '{"carbon_monoxide": true, "battery": 95, "linkquality": 115}'
```

### Documentatie

**ALTIJD bijwerken bij wijzigingen:**
- ✅ `CHANGELOG.md` + `CHANGELOG.nl.md`
- ✅ `README.md` + `README.nl.md` (als feature zichtbaar voor gebruikers)
- ✅ `docs/en/ARCHITECTURE.md` + `docs/nl/ARCHITECTURE.md` (bij technische wijzigingen)
- ✅ `docs/en/DEVELOPER.md` + `docs/nl/DEVELOPER.md` (bij ontwikkelaar workflows)
- ✅ Frontend vertalingen (`locales/en/` + `locales/nl/`)

## Troubleshooting

### Veelvoorkomende Problemen

**Frontend build faalt:**
```bash
cd smart_heating/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**WebSocket verbindt niet:**
- Controleer Home Assistant logs
- Verifieer CORS instellingen
- Check browser console voor errors

**Vertalingen tonen niet:**
- Controleer of sleutel bestaat in BEIDE `translation.json` bestanden
- Verifieer i18n initialisatie in `main.tsx`
- Check browser console voor i18n errors

**Tests falen:**
- Run `npm test -- --headed` om browser te zien
- Check Playwright versie compatibiliteit
- Verifieer test server draait op juiste poort

---

**Voor meer details, zie:**
- Engelse versie: `docs/en/DEVELOPER.md`
- Architectuur: `docs/nl/ARCHITECTURE.md`
- Gebruikers handleiding: `README.nl.md`
