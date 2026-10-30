# Meier Tobler SmartGuard

![SmartGuard: local heat-pump readings, verified HK60 mode selection and optional storage monitoring](https://raw.githubusercontent.com/martins-netizen/ha-meiertobler-smartguard/main/docs/images/overview.png)

[![HACS default catalogue](https://img.shields.io/badge/HACS-Default-41BDF5)](https://github.com/hacs/default/pull/11172)
[![Latest release](https://img.shields.io/github/v/release/martins-netizen/ha-meiertobler-smartguard)](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
[![Validation](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/workflows/validate.yml)

Connect **Meier Tobler SmartGuard 2.0** to **Home Assistant** over your local
network. Monitor your heat pump and storage temperatures, and select the
operating mode of the HK60 heating circuit. No cloud account is needed.

The graphic is an illustrative feature overview, not a live installation screenshot.

## What you get

- **Heat pump:** source inlet and condenser inlet/outlet temperatures.
- **HK60:** flow temperature, operating status, selected/effective mode and season.
  Optional room heating/cooling targets are read-only displays of settings.
- **Controller:** outdoor temperature, Smart Grid status and three fault inputs.
- **Mode control:** Auto, Normal, Reduced, Frost protection, Heating and Cooling.
  Every write is immediately read back; an unconfirmed change reports an error.
- **Optional storage:** heating-buffer and hot-water temperatures, reported
  heater indicators, diagnostic operating-hour counters and buffer heat request.
- **Local operation:** one coordinated poll every 60 seconds, UI setup,
  gateway-address reconfiguration, actionable configuration repairs and redacted
  diagnostics.

With all supported modules enabled and returning valid readings, these features
provide **16 sensors, six binary sensors and one mode select**. Heater indicators
and heat requests report gateway status; they do not measure electrical power
or energy. This integration adds no heater controls or editable temperature
setpoints. See the [operating readings guide](docs/OPERATING_READINGS.md) for
availability and interpretation.

## Installation

### New installation with HACS

1. Open **HACS** and search for **Meier Tobler SmartGuard**.
2. Download the latest stable release and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**.
4. Select **Meier Tobler SmartGuard** and enter the gateway hostname or IP address.

Enter the host only, without a URL scheme, port, path or credentials.
The integration is included in the default HACS catalogue.

### Update an existing installation

1. Open the existing **Meier Tobler SmartGuard** HACS entry and select **Update**.
2. Restart Home Assistant, then check that your entities are available.

Keep the existing integration and config entry. Your entity IDs, settings and
automations are retained. If HACS does not show an available release, use
**Update information** and check again.

See the [installation guide](docs/INSTALLATION.md) for custom-repository and
manual installation, rollback and removal.

## Compatibility and security

- **Home Assistant 2026.9.0 or newer.**
- **SmartGuard 2.0, device type `1001`.** HK60 must be enabled for its entities.
- Storage and additional operating readings are optional. Unsupported or
  unavailable optional readings do not block the original entities.
- **Trusted local network required:** the gateway REST API uses unauthenticated
  HTTP. Its UI password does not secure this API. Restrict gateway access to
  Home Assistant and never expose the API to the internet.

This is an independent community integration, not affiliated with or endorsed
by Meier Tobler AG. See the [security policy](SECURITY.md).

## Guides and support

- [Installation, updates and recovery](docs/INSTALLATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Guarded automation examples](docs/AUTOMATION_EXAMPLES.md)
- [Blueprint and quality evidence review](docs/QUALITY_REVIEW.md)
- [Additional storage measurements](docs/ADDITIONAL_MEASUREMENTS.md)
- [Additional read-only operating readings](docs/OPERATING_READINGS.md)
- [Technical reference and development checks](docs/TECHNICAL_REFERENCE.md)
- [Report a bug](https://github.com/martins-netizen/ha-meiertobler-smartguard/issues/new/choose)

Review diagnostics before sharing them. Keep hostnames, device identifiers and
raw installation data out of public issues; report security problems privately.

## Releases and verification

Use [GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
for available downloads and the [changelog](CHANGELOG.md) for changes.
Preparation and publication evidence live in the
[release checklist](docs/RELEASE_CHECKLIST.md), away from the installation steps.

- Release notes: [0.5.0](docs/RELEASE_NOTES_0.5.0.md),
  [0.4.1](docs/RELEASE_NOTES_0.4.1.md),
  [0.4.0](docs/RELEASE_NOTES_0.4.0.md), [0.3.0](docs/RELEASE_NOTES_0.3.0.md).
- HACS records: [0.4.0 upgrade](docs/HACS_TEST_V0.4.0.md),
  [0.3.0 installation](docs/HACS_TEST_V0.3.0.md).

## Deutsch – kurz erklärt

Diese lokale Integration verbindet **Meier Tobler SmartGuard 2.0** mit
**Home Assistant**. Sie zeigt Wärmepumpen- und HK60-Werte sowie optional die
Temperaturen und gemeldeten Heizeinsatzwerte von Heizpuffer und Warmwasser.
Weitere optionale Anzeigen umfassen Raum-Sollwerte, Aussentemperatur,
Smart-Grid-Status, Störsignale und Heizpuffer-Heizanforderung. Sollwerte werden
nur angezeigt; sie sind hier nicht einstellbar.
Die HK60-Betriebsmoduswahl wird nach jeder Änderung unmittelbar zurückgelesen.
Heizeinsatz-Anzeigen sind keine elektrische Leistungs- oder Energiemessung.

**Installation:** In HACS nach **Meier Tobler SmartGuard** suchen, die aktuelle
stabile Version herunterladen und Home Assistant neu starten. Bei der ersten
Installation die Integration unter **Einstellungen → Geräte & Dienste**
hinzufügen. Bei einem Update bleibt die bestehende Einrichtung erhalten.
Benötigt werden SmartGuard-Gerätetyp `1001` und Home Assistant **ab 2026.9.0**.
Die ungeschützte lokale HTTP-API gehört ausschliesslich in ein vertrauenswürdiges
lokales Netzwerk. Unabhängiges Community-Projekt ohne Herstellerunterstützung.
