# Meier Tobler SmartGuard

![SmartGuard: local heat-pump readings, verified HK60 mode selection and optional storage monitoring](https://raw.githubusercontent.com/martins-netizen/ha-meiertobler-smartguard/main/docs/images/overview.png)

[![HACS default catalogue](https://img.shields.io/badge/HACS-Default-41BDF5)](https://github.com/hacs/default/pull/11172)
[![Latest release](https://img.shields.io/github/v/release/martins-netizen/ha-meiertobler-smartguard)](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
[![Validation](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/martins-netizen/ha-meiertobler-smartguard/actions/workflows/validate.yml)

Connect **Meier Tobler SmartGuard 2.0** to **Home Assistant** over your local
network. Monitor your heat pump and storage temperatures, select the
operating mode of the HK60 heating circuit and edit its holiday period through
a guided confirmation dialog. No cloud account is needed.

The graphic is an illustrative feature overview, not a live installation screenshot.

## What you get

- **Heat pump:** source inlet and condenser inlet/outlet temperatures.
- **HK60:** actual and requested flow temperature, operating status,
  selected/effective mode and season. Optional room targets, outdoor
  thresholds, design outdoor temperature and damping durations are read-only
  displays of controller settings.
- **Configured names:** keep short measurement-first names and show circuit/storage
  assignments separately; diagnostic label sensors show the configured labels.
  Numeric readings and mode control continue to cover HK60 only.
- **Controller:** outdoor temperature, Smart Grid status and three fault inputs.
- **Mode control:** Auto, Normal, Reduced, Frost protection, Heating and Cooling.
  Every write is immediately read back; an unconfirmed change reports an error.
- **HK60 holidays:** two read-only date sensors and a whole-period editor with
  explicit confirmation, source checks and readback of both dates.
- **Optional storage:** heating-buffer and hot-water temperatures, reported
  heater indicators, diagnostic operating-hour counters and buffer heat request.
- **Local operation:** one coordinated poll every 60 seconds, UI setup,
  gateway-address reconfiguration, actionable configuration repairs and redacted
  diagnostics.

With every supported module and reading available, the integration supports
**32 numeric/enum/timestamp sensors, six diagnostic label sensors, six binary
sensors and one mode select** (45 entities). This is the supported maximum;
module availability and saved entity activation determine what you see.

Heater indicators and heat requests report gateway status; they do not measure
electrical power or energy. This integration adds no heater controls or editable
temperature setpoints. See the [operating readings guide](docs/OPERATING_READINGS.md)
and [HK60 target and limits guide](docs/HK60_FLOW_AND_LIMITS.md) for availability,
configured names and interpretation.

## Release status

| Scope | Current status |
| --- | --- |
| Latest stable download | **[0.7.1](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/tag/v0.7.1)**, published on 2026-11-02. Fixes prefilled holiday dates and the integration catalogue category. |
| Development tests on `main` | Complete suites for **HA 2026.11.0** and the supported minimum **HA 2026.9.0**; both must pass the protected Quality check. |
| Unreleased change on `main` | The two diagnostic heater operating-hour counters default to disabled only when first registered. Existing activation, IDs and names are preserved. Published 0.7.1 retains its original defaults. |

Install and update through **Settings → Marketplace** on HA 2026.11+
(HACS on older HA). Keep the existing integration entry and entity IDs.
The [changelog](CHANGELOG.md) separates changes on `main` from published releases;
the [storage guide](docs/ADDITIONAL_MEASUREMENTS.md#default-activation-in-the-next-release)
explains counter activation. A documentation or CI change does not publish an update.

The holiday editor stores the HK60 start/end dates after explicit confirmation.
Physical holiday operation still needs separate acceptance. Lighting presence
simulation, absence tracking, calendars, dashboards and adaptive preheating are
separate Home Assistant configuration; they are not supplied by this integration.

## Installation

<a id="new-installation-with-hacs"></a>

### New installation

1. On **HA 2026.11+**, open **Settings → Marketplace** and acknowledge the
   community-code notice if prompted. Search for **Meier Tobler SmartGuard**
   and verify **martins-netizen/ha-meiertobler-smartguard**.
2. Install the latest stable release. Marketplace opens setup; a first install
   of an integration not previously loaded does not normally require a restart.
3. If setup does not open, use **Settings → Devices & services → Add integration**
   and select **Meier Tobler SmartGuard**.
4. Enter the gateway hostname or IP address, without a scheme, port, path or
   credentials. Keep the gateway on a trusted local network.

On **older HA**, install through **HACS**, restart HA, then add the integration
under **Settings → Devices & services**. The project is in the default catalogue.
HA 2026.11 migrates existing HACS installations automatically; do not reinstall
HACS or recreate the SmartGuard entry.

### Update an existing installation

1. On HA 2026.11+, install the offered update under **Settings → Updates**.
   On older HA, open the existing SmartGuard **HACS** entry and choose **Update**.
2. Restart Home Assistant (Marketplace provides a repair notice), then check
   entity availability. Updates still require a restart.

Keep the existing integration/config entry, entity IDs, settings and automations.
If an older HACS entry does not offer the release, use **Update information**.
Refreshing metadata does not install files.

See the [installation guide](docs/INSTALLATION.md) for custom-repository and
manual installation, rollback and removal.

### Holiday period editor

A guided **Configure** dialog edits the complete HK60 holiday period, with a
concrete warning and explicit confirmation before any write. The two dates are
read back; partial or unknown outcomes stop without automatic retry or rollback.
The editor was introduced in 0.7.0; version 0.7.1 fixes date prefilling.
Physical holiday operation still needs separate acceptance; lighting presence
simulation is configured separately in Home Assistant.
See [the holiday contract and plan](docs/HOLIDAY_MODE_PLAN.md).

## Compatibility and security

- **Home Assistant 2026.9.0 or newer.**
- Development CI tests the complete suite on **2026.11.0** and **2026.9.0**;
  see the [development checks](docs/TECHNICAL_REFERENCE.md#development-checks).
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
- [HK60 heating-curve diagnostics](docs/HK60_HEATING_CURVE.md)
- [Holiday period editor and presence-simulation plan](docs/HOLIDAY_MODE_PLAN.md)
- [Technical reference and development checks](docs/TECHNICAL_REFERENCE.md)
- [Report a bug](https://github.com/martins-netizen/ha-meiertobler-smartguard/issues/new/choose)

Review diagnostics before sharing them. Keep hostnames, device identifiers and
raw installation data out of public issues; report security problems privately.

## Releases and verification

Use [GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases/latest)
for available downloads and the [changelog](CHANGELOG.md) for changes.
Preparation and publication evidence live in the
[release checklist](docs/RELEASE_CHECKLIST.md), away from the installation steps.

- Release notes: [0.7.1](docs/RELEASE_NOTES_0.7.1.md),
  [0.7.0](docs/RELEASE_NOTES_0.7.0.md),
  [0.6.0](docs/RELEASE_NOTES_0.6.0.md),
  [0.5.0](docs/RELEASE_NOTES_0.5.0.md),
  [0.4.1](docs/RELEASE_NOTES_0.4.1.md),
  [0.4.0](docs/RELEASE_NOTES_0.4.0.md), [0.3.0](docs/RELEASE_NOTES_0.3.0.md).
- HACS records: [0.4.0 upgrade](docs/HACS_TEST_V0.4.0.md),
  [0.3.0 installation](docs/HACS_TEST_V0.3.0.md).

## Deutsch – kurz erklärt

Diese lokale Integration verbindet **Meier Tobler SmartGuard 2.0** mit
**Home Assistant**. Sie zeigt Wärmepumpen- und HK60-Werte sowie optional die
Temperaturen und gemeldeten Heizeinsatzwerte von Heizpuffer und Warmwasser.
Weitere optionale Anzeigen umfassen Vorlauf SOLL und IST, Raum-Sollwerte,
Heiz-/Kühlschwellen, Dämpfungszeiten, Aussentemperatur, Smart-Grid-Status,
Störsignale und Heizpuffer-Heizanforderung. Konfigurierte Modulbezeichnungen
machen die Anzeigen verständlicher; bestehende Entity-IDs bleiben erhalten. Sollwerte werden
nur angezeigt; sie sind hier nicht einstellbar.
Die HK60-Betriebsmoduswahl wird nach jeder Änderung unmittelbar zurückgelesen.
Heizeinsatz-Anzeigen sind keine elektrische Leistungs- oder Energiemessung.
Ferienbeginn und -ende lassen sich über den geführten HK60-Ferieneditor mit
ausdrücklicher Bestätigung ändern. Kalender, Dashboards, Anwesenheitssimulation
und adaptives Vorheizen gehören zur separaten Home-Assistant-Konfiguration.

**Stand:** Stabile Version **0.7.1**; die auf `main` bereits geänderte
Standardaktivierung neuer Diagnosezähler ist noch nicht veröffentlicht.
Bestehende Aktivierungen, Namen und IDs bleiben erhalten.

**Installation:** [Marketplace (HA 2026.11+) / HACS (older HA)](#new-installation).
Benötigt werden SmartGuard-Gerätetyp `1001` und Home Assistant **ab 2026.9.0**.
Die ungeschützte lokale HTTP-API gehört ausschliesslich in ein vertrauenswürdiges
lokales Netzwerk. Unabhängiges Community-Projekt ohne Herstellerunterstützung.
