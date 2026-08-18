# Changelog

All notable changes to Hourly Sensor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.2] - 2026-08-18

### Fixed

- Represent every configured hourly sensor as a dedicated virtual device on the
  integration page, with its rolling sensor and recalculation button grouped on
  the device summary page.

## [v0.3.1] - 2026-08-18

### Fixed

- Categorize Hourly Sensor as a device integration instead of a service, so
  configured sensors appear as devices in Home Assistant.
- Categorize each history recalculation button as a configuration entity.

## [v0.3.0] - 2026-08-18

### Added

- Add a button for every configured hourly sensor that forces its active window
  to be recalculated from the source entity's Recorder history.

## [v0.2.2] - 2026-08-02

### Fixed

- Rebuild cumulative rolling windows from Recorder after every Home Assistant
  restart, instead of trusting potentially stale persisted buckets.
- Fill unchanged clock hours when rebuilding sparse Recorder history, preserving
  correct 1, 12, and 24-hour windows across restarts and daily meter resets.

## [v0.2.1] - 2026-08-02

### Fixed

- List configured hourly sensors under **Settings → Devices & Services →
  Integrations**, so their Configure dialog remains accessible after creation.
- Restore the active rolling window from Recorder when a cumulative sensor is
  created or its source is changed, instead of showing zero until new readings
  arrive and complete an hour.

## [v0.2.0] - 2026-08-02

### Added

- Automatically detect cumulative sources from the `total` and
  `total_increasing` Home Assistant state classes.
- Allow users to override the detected data type as instantaneous or cumulative
  for source entities with missing or incorrect metadata.
- Add a Configure dialog for editing the source, data type, statistic, rolling
  window, precision, and name of an existing sensor.

### Changed

- Cumulative sources always calculate positive reading differences and handle a
  decrease as a meter reset; the selected statistic applies to instantaneous data.
- Publish the generated rolling sensor as a measurement because its value can
  decrease when an old hour leaves the window.
- Reset stored hourly buckets when the monitored entity or its data type changes,
  preventing readings from different sources from being combined.

## [v0.1.4] - 2026-08-02

### Added

- Preserve the most recently completed period's value in the `last_period`
  attribute, even after that period leaves the rolling window.

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
