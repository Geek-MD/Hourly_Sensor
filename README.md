[![Geek-MD - Hourly Sensor](https://img.shields.io/static/v1?label=Geek-MD&message=Hourly%20Sensor&color=blue&logo=github)](https://github.com/Geek-MD/Hourly_Sensor)
[![Stars](https://img.shields.io/github/stars/Geek-MD/Hourly_Sensor?style=social)](https://github.com/Geek-MD/Hourly_Sensor)
[![Forks](https://img.shields.io/github/forks/Geek-MD/Hourly_Sensor?style=social)](https://github.com/Geek-MD/Hourly_Sensor)

[![GitHub Release](https://img.shields.io/github/release/Geek-MD/Hourly_Sensor?include_prereleases&sort=semver&color=blue)](https://github.com/Geek-MD/Hourly_Sensor/releases)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/Geek-MD/Hourly_Sensor/blob/main/LICENSE)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-blue)](https://hacs.xyz/)

[![Ruff + Mypy + Hassfest](https://github.com/Geek-MD/Hourly_Sensor/actions/workflows/ci.yaml/badge.svg)](https://github.com/Geek-MD/Hourly_Sensor/actions/workflows/ci.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

<p align="left">
  <img src="https://github.com/Geek-MD/Hourly_Sensor/blob/main/custom_components/hourly_sensor/brand/icon.png?raw=true" width="200" alt="Hourly Sensor logo">
</p>

# Hourly Sensor

**Hourly Sensor** is a custom Home Assistant integration that creates rolling
statistics from one or more numeric sensor entities. Each configured sensor is
updated on the hour and keeps only the requested number of completed clock hours.

## ✨ Features

- Create any number of hourly sensors from the Home Assistant UI.
- Recalculate each hourly sensor on demand from its source entity's Recorder
  history using the button created alongside it.
- Monitor any numeric `sensor` entity.
- Automatically distinguishes instantaneous sensors from cumulative meters by
  their Home Assistant `state_class`, with an explicit override for incomplete
  or incorrect source metadata.
- Rolling windows from **1 to 168 completed hours**.
- Automatically removes the oldest hour; a 12-hour sensor discards hour 13.
- Statistics: cumulative change, sum, average, minimum, maximum, and last value.
- Handles cumulative meter resets when using **Change**.
- Dynamically inherits the monitored sensor's unit of measurement, device class,
  and state class, including when the source loads after the helper.
- Reports `0` instead of an unknown state until completed-hour data is available.
- Shows every configuration as an integration entry rather than creating or
  claiming a device for Hourly Sensor.
- Associates the rolling sensor and recalculation button with the monitored
  sensor's existing device, so both appear on its device page and automatically
  follow its area assignment.
- Persists internal hourly buckets across Home Assistant restarts.
- Exposes `average`, `minimum`, and `maximum` attributes calculated from all
  intermediate samples in the active completed-hour window.
- Preserves the most recently completed hour's value in the `last_period`
  attribute so delayed automations can still use it.
- Every hourly entity state is stored by Home Assistant's `recorder`, unless the
  entity is explicitly excluded from recording by the user.
- English and Spanish UI translations.

## 📋 Requirements

| Requirement | Minimum version |
|-------------|-----------------|
| Home Assistant | 2026.7.0 |
| HACS (optional) | 1.6.0 |
| Python (development/CI) | 3.14.2 |

## 📦 Installation

### HACS (recommended)

1. Open **HACS → Integrations**.
2. Open the three-dot menu → **Custom repositories**.
3. Add `https://github.com/Geek-MD/Hourly_Sensor` as **Integration**.
4. Search for **Hourly Sensor**, install it, and restart Home Assistant.

### Manual

1. Copy `custom_components/hourly_sensor` to
   `<config>/custom_components/hourly_sensor`.
2. Restart Home Assistant.

## ⚙️ Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Hourly Sensor**.
3. Choose a name, source sensor, data type, statistic, rolling window, and precision.
4. Repeat **Add Integration** to create additional sensors.

An existing sensor can be changed from the integration entry's **Configure**
dialog under **Settings → Devices & Services → Integrations**. Saving the options
reloads the entry automatically. If the monitored entity or its data type changes,
Hourly Sensor discards the stored buckets from the previous source and begins a
new calculation using the current reading of the newly selected entity; values
from two different entities are never mixed.

When upgrading from version 0.3.2 or 0.3.3, existing configurations are migrated
automatically. Their old Hourly Sensor device association is removed and their
sensor and recalculation button are then attached to the current source entity's
device, so configurations do not need to be deleted and recreated.

For cumulative sources, Hourly Sensor rebuilds the active rolling window from
Home Assistant's Recorder after creation or a source change. This makes already
recorded changes (such as rain accumulated since a midnight reset) available
without waiting for another complete hour. The source entity must not be excluded
from Recorder for this backfill to be available.

Every configured hourly sensor also creates a **Recalculate from history** button.
Press it to discard the active internal window and rebuild it from the numeric
states currently available in Recorder. If Recorder has no usable source history,
the existing calculation is preserved.

### Configuration examples

Hourly Sensor is configured entirely from the UI; the following tables show the
values to select in the creation form for several common use cases. Replace the
example source entity with the entity available in your Home Assistant instance.

#### Rain accumulated during the last 24 completed hours

Use this configuration when the rain gauge is a cumulative counter with
`state_class: total` or `total_increasing`:

| Option | Example value |
|--------|---------------|
| Name | `Rain — last 24 hours` |
| Source sensor | `sensor.rain_gauge_total` |
| Data type | **Automatic** |
| Statistic | **Change** |
| Rolling window | `24` |
| Decimal places | `2` |

Automatic mode identifies the source as cumulative. Hourly Sensor sums positive
reading differences and handles a counter that returns to zero.

#### Average temperature during the last 12 completed hours

| Option | Example value |
|--------|---------------|
| Name | `Outdoor temperature — 12-hour average` |
| Source sensor | `sensor.outdoor_temperature` |
| Data type | **Automatic** |
| Statistic | **Average** |
| Rolling window | `12` |
| Decimal places | `1` |

Temperature normally has `state_class: measurement`, so Automatic mode treats it
as instantaneous and applies the selected Average statistic to all recorded
samples in the completed-hour window.

#### Sum of individual hourly reports

Use **Sum** only when every source state is an individual quantity that should be
added, rather than a continuously increasing meter:

| Option | Example value |
|--------|---------------|
| Name | `Production reports — last 6 hours` |
| Source sensor | `sensor.production_report` |
| Data type | **Instantaneous** |
| Statistic | **Sum** |
| Rolling window | `6` |
| Decimal places | `0` |

Do not use this setup for an energy, water, or rain total: summing every reading
from a cumulative meter would count the same accumulated quantity repeatedly.

#### Cumulative meter with missing or incorrect metadata

If a water or energy meter does not publish a reliable `state_class`, override
automatic detection explicitly:

| Option | Example value |
|--------|---------------|
| Name | `Water consumption — last 7 days` |
| Source sensor | `sensor.water_meter` |
| Data type | **Cumulative** |
| Statistic | **Change** |
| Rolling window | `168` |
| Decimal places | `3` |

The explicit Cumulative type always uses positive differences and reset handling,
regardless of the statistic shown in a previously saved configuration.

For an instantaneous sensor, select **Minimum**, **Maximum**, or **Last** instead
of Average when you need the lowest sample, highest sample, or latest sample from
the selected completed-hour window.

### Statistics

In **Automatic** mode, sources with `state_class: total` or
`state_class: total_increasing` are cumulative; all other sources are treated as
instantaneous. You can explicitly choose either type when a source integration
does not expose reliable metadata. Cumulative sources always produce the sum of
the positive differences between readings. If the reading decreases, Hourly
Sensor treats it as a meter reset and adds the new reading after the reset.

The statistic selector applies to instantaneous sources:

| Statistic | Intended use | Rolling result |
|-----------|--------------|----------------|
| Change | Cumulative rain, water, energy, or other meter | Sum of positive changes; meter resets are handled |
| Sum | Sensors whose individual reports must be added | Sum of every sample received |
| Average | Temperature, humidity, pressure, etc. | Average of all samples |
| Minimum | Lowest observed value | Minimum of all samples |
| Maximum | Highest observed value | Maximum of all samples |
| Last | Value at the end of the latest completed hour | Latest sample |

Only completed clock hours contribute to the result. The current partial hour is
collected in the background and enters the window when the next hour begins.

## 💾 Persistence and history

Hourly buckets are saved with Home Assistant's versioned storage API. They are
restored when the integration reloads or Home Assistant restarts, so the rolling
window does not start over. The calculated entity is updated at every hour boundary;
those states are then persisted in Home Assistant's history database by `recorder`.

If the entity is listed under `recorder.exclude`, Home Assistant will intentionally
omit its history from the database. Remove that exclusion to retain its values.

## 🗂️ Changelog

See [CHANGELOG.md](CHANGELOG.md).

## 📜 License

MIT License. See [LICENSE](LICENSE).

---

<div align="center">

💻 **Proudly developed with GitHub Copilot and ChatGPT Codex** 🚀

</div>
