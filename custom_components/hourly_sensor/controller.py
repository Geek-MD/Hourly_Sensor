"""Runtime controller for Hourly Sensor."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .model import HourlyAccumulator

_LOGGER = logging.getLogger(__name__)
_STORAGE_VERSION = 1
_SAVE_DELAY_SECONDS = 5


class HourlySensorController:
    """Track a source entity and persist hourly buckets."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry_id: str,
        source_entity: str,
        window_hours: int,
        aggregation: str,
    ) -> None:
        """Initialize the controller."""
        self.hass = hass
        self.source_entity = source_entity
        self.accumulator = HourlyAccumulator(window_hours, aggregation)
        self._store: Store[dict[str, Any]] = Store(
            hass, _STORAGE_VERSION, f"hourly_sensor.{entry_id}"
        )
        self._listeners: set[Callable[[], None]] = set()
        self._remove_callbacks: list[Callable[[], None]] = []

    async def async_initialize(self) -> None:
        """Restore data and start listeners."""
        stored = await self._store.async_load()
        if stored is not None:
            self.accumulator = HourlyAccumulator.from_dict(
                stored,
                window_hours=self.accumulator.window_hours,
                aggregation=self.accumulator.aggregation,
            )

        now = dt_util.now()
        current_value = self._numeric_state()
        if current_value is not None:
            self.accumulator.add_sample(now, current_value)

        self._remove_callbacks.extend(
            (
                async_track_state_change_event(
                    self.hass, [self.source_entity], self._async_source_changed
                ),
                async_track_time_change(
                    self.hass, self._async_hour_changed, minute=0, second=0
                ),
            )
        )

    async def async_shutdown(self) -> None:
        """Stop listeners and save immediately."""
        for remove in self._remove_callbacks:
            remove()
        self._remove_callbacks.clear()
        await self._store.async_save(self.accumulator.as_dict())

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.add(listener)

        @callback
        def remove() -> None:
            self._listeners.discard(listener)

        return remove

    @callback
    def _async_source_changed(self, event: Event[EventStateChangedData]) -> None:
        new_state = event.data["new_state"]
        if new_state is None:
            return
        value = self._parse_value(new_state.state)
        if value is None:
            return
        self.accumulator.add_sample(dt_util.as_local(new_state.last_updated), value)
        self._updated()

    @callback
    def _async_hour_changed(self, now: datetime) -> None:
        self.accumulator.close_hour(now, self._numeric_state())
        self._updated()

    @callback
    def _updated(self) -> None:
        self._store.async_delay_save(
            self.accumulator.as_dict, _SAVE_DELAY_SECONDS
        )
        for listener in self._listeners:
            listener()

    def _numeric_state(self) -> float | None:
        state = self.hass.states.get(self.source_entity)
        return None if state is None else self._parse_value(state.state)

    @staticmethod
    def _parse_value(raw: str) -> float | None:
        if raw in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            _LOGGER.debug("Ignoring non-numeric source state: %s", raw)
            return None
