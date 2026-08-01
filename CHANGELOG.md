# Changelog

All notable changes to Hourly Sensor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.3] - 2026-08-01

### Fixed

- Dynamically expose the source sensor's `unit_of_measurement`, `device_class`,
  and `state_class`, even if the source entity is not available while the helper
  is being constructed.

## [v0.1.2] - 2026-08-01

### Fixed

- Make every configured sensor inherit the source sensor's unit of measurement
  and device class without adding a rolling-window suffix.
- Report `0` instead of an unknown state while a rolling window has no completed
  data, including windows longer than one hour.

## [v0.1.1] - 2026-08-01

### Fixed

- Normalize the rolling-window and precision selector values to integers.
- Prevent existing configurations with a decimal hour value from raising an
  invalid slice-index error while adding the sensor entity.

## [v0.1.0] - 2026-07-31

### Added

- Initial release of **Hourly Sensor**.
- UI configuration for creating any number of rolling hourly sensors.
- Rolling windows from 1 to 168 completed clock hours.
- Change, sum, average, minimum, maximum, and last-value statistics.
- Persistent hourly buckets that survive Home Assistant restarts.
- Local-time hour boundaries, including timezone-offset changes.
- Automatic source-device association using the Home Assistant 2026.8 helper API.
- Contextual rolling units such as `mm/h` and `mm/12h`.
- Average, minimum, and maximum attributes from intermediate source samples.
- English and Spanish translations.
- Geek-MD family brand icon and logo for HACS and Home Assistant.
- HACS metadata and Ruff, mypy, pytest, hassfest, and HACS workflows.
- Python 3.14.2 and Node.js 24-compatible GitHub Actions.
