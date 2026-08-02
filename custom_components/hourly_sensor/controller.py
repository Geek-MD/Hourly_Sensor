"""Runtime controller for Hourly Sensor."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.recorder import history
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    AGGREGATION_CHANGE,
    SOURCE_TYPE_AUTO,
    SOURCE_TYPE_CUMULATIVE,
    SOURCE_TYPE_INSTANTANEOUS,
)
from .model import HourlyAccumulator, hour_start

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
        source_type: str,
    ) -> None:
        """Initialize the controller."""
        self.hass = hass
        self.source_entity = source_entity
        self.configured_aggregation = aggregation
        self.configured_source_type = source_type
        self.source_type = self._resolve_source_type()
        effective_aggregation = (
            AGGREGATION_CHANGE
            if self.source_type == SOURCE_TYPE_CUMULATIVE
            else aggregation
        )
        self.accumulator = HourlyAccumulator(window_hours, effective_aggregation)
        self._store: Store[dict[str, Any]] = Store(
            hass, _STORAGE_VERSION, f"hourly_sensor.{entry_id}"
        )
        self._listeners: set[Callable[[], None]] = set()
        self._remove_callbacks: list[Callable[[], None]] = []

    async def async_initialize(self) -> None:
        """Restore data and start listeners."""
        stored = await self._store.async_load()
        restored = False
        if stored is not None:
            stored_source = stored.get("source_entity")
            stored_type = stored.get("source_type")
            # Storage from releases before editing support has no identity
            # metadata and remains compatible. Once metadata exists, changing
            # the source/type starts a clean calculation for the new entity.
            if self._can_restore(stored_source, stored_type):
                raw_accumulator = stored.get("accumulator", stored)
                self.accumulator = HourlyAccumulator.from_dict(
                    raw_accumulator,
                    window_hours=self.accumulator.window_hours,
                    aggregation=self.accumulator.aggregation,
                )
                restored = True

        now = dt_util.now()
        if not restored and self.source_type == SOURCE_TYPE_CUMULATIVE:
            await self._async_restore_history(now)
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

    async def _async_restore_history(self, now: datetime) -> None:
        """Rebuild a cumulative window after creation or source replacement."""
        try:
            recorder = get_instance(self.hass)
        except KeyError:
            return

        start = hour_start(now) - timedelta(hours=self.accumulator.window_hours)
        states = await recorder.async_add_executor_job(
            history.get_significant_states,
            self.hass,
            start,
            now,
            [self.source_entity],
        )
        self._add_historical_states(states.get(self.source_entity, []))

    def _add_historical_states(self, states: list[State | dict[str, Any]]) -> None:
        """Add numeric recorder states to the fresh accumulator in time order."""
        for state in states:
            if not isinstance(state, State):
                continue
            value = self._parse_value(state.state)
            if value is not None:
                self.accumulator.add_sample(dt_util.as_local(state.last_updated), value)

    async def async_shutdown(self) -> None:
        """Stop listeners and save immediately."""
        for remove in self._remove_callbacks:
            remove()
        self._remove_callbacks.clear()
        await self._store.async_save(self._storage_data())

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
        self._refresh_auto_source_type()
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
        self._store.async_delay_save(self._storage_data, _SAVE_DELAY_SECONDS)
        for listener in self._listeners:
            listener()

    def _numeric_state(self) -> float | None:
        state = self.hass.states.get(self.source_entity)
        return None if state is None else self._parse_value(state.state)

    def _resolve_source_type(self) -> str:
        """Resolve automatic mode from Home Assistant's state class metadata."""
        if self.configured_source_type != SOURCE_TYPE_AUTO:
            return self.configured_source_type
        state = self.hass.states.get(self.source_entity)
        state_class = None if state is None else state.attributes.get("state_class")
        if state_class in ("total", "total_increasing"):
            return SOURCE_TYPE_CUMULATIVE
        return SOURCE_TYPE_INSTANTANEOUS

    def _refresh_auto_source_type(self) -> None:
        """Detect metadata that appeared after setup, before collecting data."""
        if self.configured_source_type != SOURCE_TYPE_AUTO or self.accumulator.buckets:
            return
        self.source_type = self._resolve_source_type()
        self.accumulator.aggregation = (
            AGGREGATION_CHANGE
            if self.source_type == SOURCE_TYPE_CUMULATIVE
            else self.configured_aggregation
        )

    def _storage_data(self) -> dict[str, Any]:
        """Include source identity so edited entries cannot reuse stale data."""
        return {
            "source_entity": self.source_entity,
            "source_type": self.source_type,
            "accumulator": self.accumulator.as_dict(),
        }

    def _can_restore(self, stored_source: Any, stored_type: Any) -> bool:
        """Return whether persisted samples belong to this configuration."""
        return stored_source in (None, self.source_entity) and stored_type in (
            None,
            self.source_type,
        )

    @staticmethod
    def _parse_value(raw: str) -> float | None:
        if raw in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        try:
            return float(raw)
        except TypeError, ValueError:
            _LOGGER.debug("Ignoring non-numeric source state: %s", raw)
            return None
