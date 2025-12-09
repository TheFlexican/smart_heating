# Slimme Verwarming

[![Versie](https://img.shields.io/badge/versie-0.5.12-blue.svg)](https://github.com/TheFlexican/smart_heating/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Licentie](https://img.shields.io/badge/licentie-MIT-green.svg)](LICENSE)

Een Home Assistant custom integratie voor intelligente multi-zone verwarmingsregeling met adaptief leren. Bevat een moderne React-gebaseerde webinterface voor eenvoudige configuratie en real-time monitoring.

[🇬🇧 English version](README.md) | [📚 Volledige Documentatie](docs/nl/)

## Functies

### 🏠 Slimme Zone Controle
- **Multi-zone verwarmingsbeheer** - Creëer en beheer onbeperkte verwarmingszones
- **Universele apparaatondersteuning** - Werkt met ELKE Home Assistant climate integratie (Nest, Ecobee, Zigbee2MQTT, etc.)
- **Real-time status updates** - WebSocket-gebaseerde live monitoring met <3s responstijd
- **Handmatige override detectie** - Detecteert automatisch en respecteert externe thermostaat wijzigingen

### 📅 Intelligente Planning
- **Flexibele schema's** - Tijdgebaseerde temperatuur profielen met meerdaagse ondersteuning
- **Preset modus planning** - Gebruik preset modi (Weg, Eco, Comfort) in plaats van vaste temperaturen
- **Datumspecifieke schema's** - Eenmalige schema's voor feestdagen en speciale evenementen
- **Dag-overschrijdende ondersteuning** - Schema's kunnen middernacht overschrijden (bijv. Zaterdag 22:00 - Zondag 07:00)

### 🧠 Adaptief Leren
- **Machine learning** - Leert verwarmingspatronen en buitentemperatuur correlatie
- **Slimme nacht boost** - Voorspelt optimale verwarmingsstarttijd voor ochtend schema's
- **Weerbewust** - Gebruikt buitentemperatuur om verwarmingsefficiëntie te optimaliseren
- **Persistent leren** - Slaat data op met Home Assistant Statistics API

### 🎯 Preset Modi & Automatisering
- **6 preset modi** - Weg, Eco, Comfort, Thuis, Slapen, Activiteit (+ Boost)
- **Globale presets** - Configureer standaard temperaturen eenmaal, pas toe op alle zones
- **Multi-gebruiker ondersteuning** - Individuele temperatuurvoorkeuren per gebruiker met automatische aanwezigheidsdetectie
- **Aanwezigheidsdetectie** - Automatische modus wisseling gebaseerd op aanwezigheid
- **Raam sensoren** - Auto-aanpassen of pauzeren verwarming bij open ramen/deuren

### 📊 Analytics & Inzichten
- **Efficiëntie rapporten** - Analyseer verwarmingsprestaties met 0-100 energie scores
- **Historische vergelijkingen** - Vergelijk prestaties over verschillende tijdsperioden
- **Prestatie metrieken** - Volg verwarmingstijd, cycli, temperatuurverschillen
- **Slimme aanbevelingen** - Automatische suggesties om efficiëntie te verbeteren
- **Trend visualisatie** - Grafieken en tabellen die verwarmingspatronen over tijd tonen

### 🔒 Veiligheid & Controle
- **Vorstbescherming** - Globale minimumtemperatuur om bevriezing te voorkomen
- **Nooduitschakeling** - Rook/CO detector integratie voor veiligheid
- **HVAC modus ondersteuning** - Verwarmen, koelen, auto, en uit modi
- **Slimme schakelaar controle** - Auto-uitschakeling circulatiepompen bij niet verwarmen

### 📊 Monitoring & Debugging
- **Temperatuur geschiedenis** - Volg en visualiseer trends (5-min resolutie, 1-365 dagen bewaring)
  - **JSON opslag** (standaard) - Eenvoudige bestandsopslag voor alle HA installaties
  - **Database opslag** (optioneel) - MariaDB/PostgreSQL/MySQL ondersteuning voor power users
    - Automatische database detectie via Home Assistant's recorder configuratie
    - Geoptimaliseerd schema met geïndexeerde kolommen voor snelle queries
    - Niet-blokkerende operaties via recorder's database engine
  - **Naadloze migratie** - Schakel tussen opslag backends zonder dataverlies
    - Bidirectionele migratie API (JSON ↔ Database)
    - Automatische validatie voor migratie
    - Data blijft behouden na herstarts
- **Ontwikkelings logs** - Per-zone logging met gedetailleerde strategie beslissingen
- **Interactieve grafieken** - Aanpasbare tijdsbereiken met preset filters
- **Event filtering** - Kleur-gecodeerde event types met één-klik filtering

### 🎨 Moderne Web Interface
- **React-gebaseerde GUI** - Snel, responsief, en intuïtief
- **Material-UI design** - Schone, moderne interface met dark mode ondersteuning
- **Drag-and-drop** - Eenvoudige apparaat toewijzing en schema beheer
- **Real-time updates** - Live status via WebSocket, geen pagina verversing nodig
- **Internationalisatie** - Volledige ondersteuning voor Engels en Nederlands

### 🔄 Back-up & Herstel
- **Configuratie export** - Download complete instellingen als JSON
- **Import met preview** - Bekijk wijzigingen voor toepassing
- **Automatische backups** - Gemaakt voor elke import voor veiligheid
- **Versie compatibiliteit** - Slimme detectie van configuratie versies

## Snel Starten

### Installatie

1. **HACS (Aanbevolen)**
   - Voeg custom repository toe: `https://github.com/TheFlexican/smart_heating`
   - Zoek naar "Smart Heating" in HACS
   - Installeer en herstart Home Assistant

2. **Handmatige Installatie**
   ```bash
   cd /config/custom_components
   git clone https://github.com/TheFlexican/smart_heating.git
   ```

3. **Configuratie**
   - Ga naar Instellingen → Apparaten & Services → Integratie Toevoegen
   - Zoek naar "Smart Heating"
   - Configureer initiële instellingen

### Toegang Web Interface

Navigeer naar: `http://your-home-assistant:8123/api/smart_heating/`

## Belangrijke Instellingen

### Globale Instellingen
- **Preset Temperaturen** - Standaard temps voor Weg, Eco, Comfort, Thuis, Slapen, Activiteit
- **Aanwezigheid Sensoren** - Configureer eenmaal, pas toe op alle zones
- **Vorstbescherming** - Minimumtemperatuur (standaard: 7°C)
- **Hysterese** - Temperatuur buffer om snel aan/uit schakelen te voorkomen (0.1-2.0°C)
- **Veiligheids Sensoren** - Rook/CO detectoren voor nooduitschakeling

### Zone Instellingen
- **Doeltemperatuur** - Basis temperatuur voor de zone
- **Apparaten** - Wijs thermostaten, sensoren, kleppen, schakelaars toe
- **Schema's** - Tijdgebaseerde temperatuur of preset profielen
- **Nacht Boost** - Voorverwarming met additieve offset tijdens geconfigureerde uren (werkt met schema's)
- **Boost Modus** - Tijdelijke hoge-temperatuur boost (configureerbare duur)
- **Raam Sensoren** - Auto-aanpassen bij open ramen/deuren
- **Aanwezigheidsdetectie** - Kies globale of zone-specifieke sensoren
- **Schakelaar Controle** - Auto-uitschakeling pompen bij niet verwarmen

### Geavanceerde Functies
- **Slimme Nacht Boost (AI)** - Voorspelt optimale verwarmingsstarttijd met leergegevens
- **Handmatige Override** - Systeem respecteert externe thermostaat aanpassingen
- **Vakantiemodus** - Stel start/eind datums in met weg temperatuur
- **Hysterese Override** - Per-zone aangepaste waarden (nuttig voor vloerverwarming)
- **Importeren/Exporteren** - Back-up en herstel complete configuratie met één klik

## Ondersteunde Apparaten

### Climate Entiteiten
- ✅ **Alle HA climate integraties** - Google Nest, Ecobee, generic_thermostat, Z-Wave, Zigbee2MQTT
- ✅ **Thermostaten** - Elke climate.* entiteit met temperatuur controle
- ✅ **AC units** - Ondersteunt verwarmen, koelen, en auto modi

### Sensoren
- ✅ **Temperatuur sensoren** - sensor.* entiteiten met device_class: temperature
- ✅ **Raam/deur sensoren** - binary_sensor.* voor open/dicht detectie
- ✅ **Aanwezigheid sensoren** - Persoon, device_tracker, bewegingssensoren
- ✅ **Veiligheids sensoren** - Rookmelders, CO detectoren (binary_sensor.*)

### Andere Apparaten
- ✅ **Kleppen** - number.* of climate.* entiteiten met positie controle
- ✅ **Schakelaars** - switch.* voor pompen, relais, etc.
- ✅ **Weer** - Voor buitentemperatuur in adaptief leren

## Documentatie

### Gebruikershandleidingen
- 📖 [Volledige Documentatie](docs/nl/) - Complete functie handleiding
- 🏗️ [Architectuur](docs/nl/ARCHITECTURE.md) - Technisch ontwerp en componenten
- 💻 [Ontwikkelaars Handleiding](DEVELOPER.md) - Development setup en workflow
- 📝 [Changelog](CHANGELOG.nl.md) - Versie geschiedenis en release notes

### Snelle Referenties
- ⚡ [Test Handleiding](TESTING_QUICKSTART.md) - Run tests en verifieer coverage
- 🔧 [API Referentie](docs/nl/ARCHITECTURE.md#api-endpoints) - REST API endpoints
- 🐛 [Probleemoplossing](docs/nl/#probleemoplossing) - Veelvoorkomende problemen en oplossingen

## REST API

Volledige REST API voor programmatische controle:

```bash
# Haal alle zones op
GET /api/smart_heating/areas

# Update zone temperatuur
POST /api/smart_heating/areas/{area_id}/temperature
{"temperature": 21.5}

# Activeer boost modus
POST /api/smart_heating/areas/{area_id}/boost
{"duration": 60, "temperature": 24}

# Voeg schema toe
POST /api/smart_heating/areas/{area_id}/schedule
{
  "days": ["monday", "tuesday"],
  "start_time": "07:00",
  "end_time": "09:00",
  "preset_mode": "comfort"
}

# Gebruikersbeheer
GET /api/smart_heating/users
POST /api/smart_heating/users
GET /api/smart_heating/users/{user_id}
GET /api/smart_heating/users/active_preferences

# Analytics
GET /api/smart_heating/efficiency/report/{area_id}
GET /api/smart_heating/efficiency/all_areas
GET /api/smart_heating/comparison/{period}
POST /api/smart_heating/comparison/custom
```

Zie [API Documentatie](docs/nl/ARCHITECTURE.md#api-endpoints) voor complete endpoint lijst.

## Bijdragen

Bijdragen zijn welkom! Zie [DEVELOPER.md](DEVELOPER.md) voor development setup.

### Development Workflow
```bash
# Clone repository
git clone https://github.com/TheFlexican/smart_heating.git

# Installeer dependencies
cd smart_heating/frontend
npm install

# Run tests
cd ../..
./run_tests.sh  # Python unit tests
cd tests/e2e && npm test  # E2E tests

# Format en lint (pre-commit hooks)
git commit -m "Jouw wijzigingen"  # Auto-runs black + ruff
```

## Licentie

MIT Licentie - zie [LICENSE](LICENSE) bestand voor details.

## Ondersteuning

- 🐛 [Meld bugs](https://github.com/TheFlexican/smart_heating/issues)
- 💡 [Vraag functies aan](https://github.com/TheFlexican/smart_heating/issues)
- 📖 [Volledige documentatie](docs/nl/)
- 🇬🇧 [English documentation](docs/en/)

## Links

- [GitHub Repository](https://github.com/TheFlexican/smart_heating)
- [HACS Integratie](https://hacs.xyz/)
- [Home Assistant](https://www.home-assistant.io/)
- [Releases](https://github.com/TheFlexican/smart_heating/releases)
