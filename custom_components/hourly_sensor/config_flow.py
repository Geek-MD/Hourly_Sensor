"""Config flow for Hourly Sensor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    AGGREGATIONS,
    CONF_AGGREGATION,
    CONF_HOURS,
    CONF_NAME,
    CONF_PRECISION,
    CONF_SOURCE_ENTITY,
    DEFAULT_AGGREGATION,
    DEFAULT_HOURS,
    DEFAULT_PRECISION,
    DOMAIN,
    MAX_HOURS,
    MAX_PRECISION,
    MIN_HOURS,
    MIN_PRECISION,
)


class HourlySensorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an Hourly Sensor config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create one rolling hourly sensor."""
        errors: dict[str, str] = {}
        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]
            state = self.hass.states.get(source_entity)
            if state is None:
                errors[CONF_SOURCE_ENTITY] = "entity_not_found"
            else:
                try:
                    float(state.state)
                except TypeError, ValueError:
                    errors[CONF_SOURCE_ENTITY] = "source_not_numeric"

            if not errors:
                # Number selectors return floats; persist discrete settings as
                # integers so config entries retain their declared types.
                user_input[CONF_HOURS] = int(user_input[CONF_HOURS])
                user_input[CONF_PRECISION] = int(user_input[CONF_PRECISION])
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_SOURCE_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_AGGREGATION, default=DEFAULT_AGGREGATION
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(AGGREGATIONS), translation_key="aggregation"
                    )
                ),
                vol.Required(CONF_HOURS, default=DEFAULT_HOURS): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_HOURS,
                        max=MAX_HOURS,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(CONF_PRECISION, default=DEFAULT_PRECISION): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_PRECISION,
                        max=MAX_PRECISION,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
