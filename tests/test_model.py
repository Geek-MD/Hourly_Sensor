"""Tests for the hourly aggregation model."""

from datetime import datetime

import pytest

from custom_components.hourly_sensor.const import (
    AGGREGATION_AVERAGE,
    AGGREGATION_CHANGE,
    AGGREGATION_LAST,
    AGGREGATION_MAXIMUM,
    AGGREGATION_MINIMUM,
    AGGREGATION_SUM,
)
from custom_components.hourly_sensor.model import HourlyAccumulator


def _moment(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 31, hour, minute)  # noqa: DTZ001


def test_change_rolls_window_and_handles_reset() -> None:
    """Change sums growth and removes the hour outside the window."""
    accumulator = HourlyAccumulator(2, AGGREGATION_CHANGE)
    accumulator.add_sample(_moment(10), 10)
    accumulator.add_sample(_moment(10, 30), 13)
    accumulator.add_sample(_moment(11), 13)
    accumulator.add_sample(_moment(11, 30), 1)  # Meter reset: add new value.
    accumulator.add_sample(_moment(12), 1)

    assert accumulator.value == 4

    accumulator.add_sample(_moment(12, 30), 6)
    accumulator.add_sample(_moment(13), 6)

    assert accumulator.value == 6
    assert accumulator.completed_hours == 2


def test_cumulative_baseline_is_carried_across_hour_boundary() -> None:
    """Each hour includes growth from its boundary baseline and handles resets."""
    accumulator = HourlyAccumulator(2, AGGREGATION_CHANGE)
    accumulator.add_sample(_moment(10, 45), 100)
    accumulator.close_hour(_moment(11), 105)
    accumulator.add_sample(_moment(11, 30), 2)
    accumulator.close_hour(_moment(12), 4)

    assert accumulator.value == 9

    accumulator.close_hour(_moment(13), 4)

    assert accumulator.value == 4


@pytest.mark.parametrize(
    ("aggregation", "expected"),
    [
        (AGGREGATION_SUM, 10),
        (AGGREGATION_AVERAGE, 2.5),
        (AGGREGATION_MINIMUM, 1),
        (AGGREGATION_MAXIMUM, 4),
        (AGGREGATION_LAST, 4),
    ],
)
def test_sample_aggregations(aggregation: str, expected: float) -> None:
    """Sample aggregations use all samples from completed hours."""
    accumulator = HourlyAccumulator(2, aggregation)
    accumulator.add_sample(_moment(10), 1)
    accumulator.add_sample(_moment(10, 30), 2)
    accumulator.add_sample(_moment(11), 3)
    accumulator.add_sample(_moment(11, 30), 4)
    accumulator.add_sample(_moment(12), 5)

    assert accumulator.value == expected


def test_storage_round_trip() -> None:
    """Stored buckets restore without losing the rolling value."""
    accumulator = HourlyAccumulator(1, AGGREGATION_CHANGE)
    accumulator.add_sample(_moment(10), 10)
    accumulator.add_sample(_moment(10, 30), 12)
    accumulator.add_sample(_moment(11), 12)

    restored = HourlyAccumulator.from_dict(
        accumulator.as_dict(), window_hours=1, aggregation=AGGREGATION_CHANGE
    )

    assert restored.value == 2
    assert restored.last_period == 2


def test_existing_storage_derives_last_period() -> None:
    """Storage written before v0.1.4 provides the latest completed value."""
    restored = HourlyAccumulator.from_dict(
        {
            "buckets": [
                {
                    "start": _moment(10).isoformat(),
                    "samples": [10, 15],
                    "complete": True,
                }
            ]
        },
        window_hours=1,
        aggregation=AGGREGATION_CHANGE,
    )

    assert restored.last_period == 5


def test_last_period_survives_rolling_window_pruning() -> None:
    """The last closed period remains available after its bucket is discarded."""
    accumulator = HourlyAccumulator(1, AGGREGATION_CHANGE)
    accumulator.add_sample(_moment(10), 10)
    accumulator.add_sample(_moment(10, 30), 14)
    accumulator.add_sample(_moment(11), 14)

    assert accumulator.last_period == 4

    accumulator.add_sample(_moment(11, 30), 20)
    accumulator.add_sample(_moment(12), 20)

    assert accumulator.last_period == 6
    assert all(
        bucket.start != _moment(10).isoformat() for bucket in accumulator.buckets
    )


def test_number_selector_float_window_is_normalized() -> None:
    """A NumberSelector float can be used to select the completed window."""
    accumulator = HourlyAccumulator(1.0, AGGREGATION_CHANGE)  # type: ignore[arg-type]
    accumulator.add_sample(_moment(10), 10)
    accumulator.add_sample(_moment(10, 30), 12)
    accumulator.add_sample(_moment(11), 12)

    assert accumulator.window_hours == 1
    assert accumulator.value == 2


@pytest.mark.parametrize("window_hours", [1, 2, 12, 168])
def test_empty_completed_window_returns_zero(window_hours: int) -> None:
    """A window without completed data has a numeric zero state."""
    accumulator = HourlyAccumulator(window_hours, AGGREGATION_CHANGE)

    assert accumulator.value == 0

    accumulator.add_sample(_moment(10), 10)

    assert accumulator.value == 0


def test_intermediate_sample_statistics_ignore_partial_hour() -> None:
    """Attribute statistics use only completed-hour intermediate samples."""
    accumulator = HourlyAccumulator(1, AGGREGATION_CHANGE)
    accumulator.add_sample(_moment(10), 1)
    accumulator.add_sample(_moment(10, 15), 3)
    accumulator.add_sample(_moment(10, 45), 5)
    accumulator.add_sample(_moment(11), 100)

    assert accumulator.sample_statistics == {
        "average": 3,
        "minimum": 1,
        "maximum": 5,
    }
