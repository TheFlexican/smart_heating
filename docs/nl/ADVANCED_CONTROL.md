# Geavanceerde ketelbesturing (verwarmingscurve, PWM, PID, OPV)

Deze pagina beschrijft de nieuwe optionele functies voor geavanceerde besturing van Smart Heating. Deze functies zijn standaard uitgeschakeld en moeten in Global Settings worden ingeschakeld.

## Functies

- Verwarmingscurve: berekent ketelwatertemperatuur op basis van doeltemperatuur en buitentemperatuur, met configureerbare coëfficiënt.
- PID-regeling: optionele PID-lus met automatische gains.
- PWM (Pulse Width Modulation): voor ketels zonder modulation, een ON/OFF duty-cycle approximation.
- OPV: kalibratieroutine om Overshoot Protection Value te berekenen.

## Stroomtemperatuur Standaarden & Aanbevelingen

- De integratie bevat nu bijgewerkte praktische standaarden voor de aanvoertemperatuur afhankelijk van het type verwarmingssysteem:
	- Vloerverwarming: standaard basis aanvoertemperatuur is ingesteld op 40°C. Dit is een praktische waarde binnen 35-45°C en verwarmt ruimtes doorgaans sneller dan de eerder zeer lage waarden.
	- Radiatoren: standaard basis aanvoertemperatuur is ingesteld op 55°C. Radiatoren hebben meestal hogere watertemperaturen nodig (50-70°C) afhankelijk van radiatorafmetingen en systeemontwerp.

Als het systeem te langzaam opwarmt, controleer of `heating_type` per zone correct is ingesteld en overweeg de `heating_curve_coefficient` te verfijnen of per-gebied minimumeigenschappen aan te passen.

## Configuratie

Zie Global Settings > Advanced Control in de UI.
