"""Pure data model for Hourly Sensor."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from statistics import fmean
from typing import Any

from .const import (
    AGGREGATION_AVERAGE,
    AGGREGATION_CHANGE,
    AGGREGATION_LAST,
    AGGREGATION_MAXIMUM,
    AGGREGATION_MINIMUM,
    AGGREGATION_SUM,
)


def hour_start(moment: datetime) -> datetime:
    """Return the start of the local hour represented by moment."""
    return moment.replace(minute=0, second=0, microsecond=0)


@dataclass(slots=True)
class HourBucket:
    """Samples collected during one clock hour."""

    start: str
    samples: list[float] = field(default_factory=list)
    complete: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> HourBucket:
        """Deserialize a bucket from storage."""
        return cls(
            start=str(raw["start"]),
            samples=[float(value) for value in raw.get("samples", [])],
            complete=bool(raw.get("complete", False)),
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialize a bucket for storage."""
        return asdict(self)


@dataclass(slots=True)
class HourlyAccumulator:
    """Collect samples into hours and calculate a rolling statistic."""

    window_hours: int
    aggregation: str
    buckets: list[HourBucket] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize values supplied by Home Assistant selectors."""
        # NumberSelector serializes its result as a float, even when configured
        # with a step of one.  Keep the model's window usable as a slice index.
        self.window_hours = int(self.window_hours)

    @classmethod
    def from_dict(
        cls, raw: dict[str, Any], *, window_hours: int, aggregation: str
    ) -> HourlyAccumulator:
        """Restore an accumulator while honoring the current configuration."""
        accumulator = cls(
            window_hours=window_hours,
            aggregation=aggregation,
            buckets=[HourBucket.from_dict(item) for item in raw.get("buckets", [])],
        )
        accumulator._prune()
        return accumulator

    def as_dict(self) -> dict[str, Any]:
        """Serialize the accumulator."""
        return {"buckets": [bucket.as_dict() for bucket in self.buckets]}

    def add_sample(self, moment: datetime, value: float) -> None:
        """Add one numeric sample, closing elapsed hourly buckets."""
        start = hour_start(moment).isoformat()
        current = self._current
        if current is None or current.start != start:
            if current is not None:
                current.complete = True
            self.buckets.append(HourBucket(start=start, samples=[value]))
        else:
            current.samples.append(value)
        self._prune()

    def close_hour(self, moment: datetime, current_value: float | None) -> None:
        """Close the previous hour and initialize the new one."""
        start = hour_start(moment).isoformat()
        current = self._current
        if current is not None and current.start != start:
            current.complete = True
        if current is None or current.start != start:
            samples = [] if current_value is None else [current_value]
            self.buckets.append(HourBucket(start=start, samples=samples))
        self._prune()

    @property
    def value(self) -> float | None:
        """Return the statistic for the configured completed-hour window."""
        complete = [
            bucket for bucket in self.buckets if bucket.complete and bucket.samples
        ]
        selected = complete[-self.window_hours :]
        if not selected:
            return 0.0

        if self.aggregation == AGGREGATION_CHANGE:
            return sum(self._change(bucket.samples) for bucket in selected)

        samples = [sample for bucket in selected for sample in bucket.samples]
        if self.aggregation == AGGREGATION_SUM:
            return sum(samples)
        if self.aggregation == AGGREGATION_AVERAGE:
            return fmean(samples)
        if self.aggregation == AGGREGATION_MINIMUM:
            return min(samples)
        if self.aggregation == AGGREGATION_MAXIMUM:
            return max(samples)
        if self.aggregation == AGGREGATION_LAST:
            return samples[-1]
        raise ValueError(f"Unsupported aggregation: {self.aggregation}")

    @property
    def sample_statistics(self) -> dict[str, float] | None:
        """Return average, minimum, and maximum for samples in the window."""
        samples = self._window_samples
        if not samples:
            return None
        return {
            "average": fmean(samples),
            "minimum": min(samples),
            "maximum": max(samples),
        }

    @property
    def completed_hours(self) -> int:
        """Return how many retained completed hours contain data."""
        return sum(bucket.complete and bool(bucket.samples) for bucket in self.buckets)

    @property
    def last_completed_hour(self) -> str | None:
        """Return the timestamp of the latest completed bucket."""
        for bucket in reversed(self.buckets):
            if bucket.complete and bucket.samples:
                return bucket.start
        return None

    @property
    def _current(self) -> HourBucket | None:
        return self.buckets[-1] if self.buckets else None

    @property
    def _window_samples(self) -> list[float]:
        complete = [
            bucket for bucket in self.buckets if bucket.complete and bucket.samples
        ]
        return [
            sample
            for bucket in complete[-self.window_hours :]
            for sample in bucket.samples
        ]

    def _prune(self) -> None:
        # Retain the requested completed hours plus the current partial hour.
        maximum = self.window_hours + 1
        if len(self.buckets) > maximum:
            self.buckets = self.buckets[-maximum:]

    @staticmethod
    def _change(samples: list[float]) -> float:
        """Calculate growth, treating a decrease as a meter reset."""
        if len(samples) < 2:
            return 0.0
        total = 0.0
        previous = samples[0]
        for sample in samples[1:]:
            total += sample - previous if sample >= previous else sample
            previous = sample
        return total
