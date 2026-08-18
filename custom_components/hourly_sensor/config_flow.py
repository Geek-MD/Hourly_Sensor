"""Config flow for Hourly Sensor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
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
    CONF_SOURCE_TYPE,
    DEFAULT_AGGREGATION,
    DEFAULT_HOURS,
    DEFAULT_PRECISION,
    DEFAULT_SOURCE_TYPE,
    DOMAIN,
    MAX_HOURS,
    MAX_PRECISION,
    MIN_HOURS,
    MIN_PRECISION,
    SOURCE_TYPES,
)


class HourlySensorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an Hourly Sensor config flow."""

    VERSION = 3

    @staticmethod
    @callback
    def async_get_options_flow(_config_entry: Any) -> OptionsFlow:
        """Create the flow used to edit an existing hourly sensor."""
        return HourlySensorOptionsFlow()

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

        return self.async_show_form(
            step_id="user",
            data_schema=_configuration_schema(),
            errors=errors,
        )


class HourlySensorOptionsFlow(OptionsFlowWithReload):
    """Allow an existing hourly sensor to be edited and reloaded."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and save edited sensor settings."""
        errors: dict[str, str] = {}
        if user_input is not None:
            state = self.hass.states.get(user_input[CONF_SOURCE_ENTITY])
            if state is None:
                errors[CONF_SOURCE_ENTITY] = "entity_not_found"
            else:
                try:
                    float(state.state)
                except TypeError, ValueError:
                    errors[CONF_SOURCE_ENTITY] = "source_not_numeric"
            if not errors:
                user_input[CONF_HOURS] = int(user_input[CONF_HOURS])
                user_input[CONF_PRECISION] = int(user_input[CONF_PRECISION])
                self.hass.config_entries.async_update_entry(
                    self.config_entry, title=user_input[CONF_NAME]
                )
                return self.async_create_entry(data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            defaults.update(user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_configuration_schema(defaults),
            errors=errors,
        )


def _configuration_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the shared create/edit schema with optional current values."""
    values = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=values.get(CONF_NAME, vol.UNDEFINED)): str,
            vol.Required(
                CONF_SOURCE_ENTITY,
                default=values.get(CONF_SOURCE_ENTITY, vol.UNDEFINED),
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_SOURCE_TYPE,
                default=values.get(CONF_SOURCE_TYPE, DEFAULT_SOURCE_TYPE),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=list(SOURCE_TYPES), translation_key="source_type"
                )
            ),
            vol.Required(
                CONF_AGGREGATION,
                default=values.get(CONF_AGGREGATION, DEFAULT_AGGREGATION),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=list(AGGREGATIONS), translation_key="aggregation"
                )
            ),
            vol.Required(
                CONF_HOURS, default=values.get(CONF_HOURS, DEFAULT_HOURS)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_HOURS,
                    max=MAX_HOURS,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_PRECISION,
                default=values.get(CONF_PRECISION, DEFAULT_PRECISION),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_PRECISION,
                    max=MAX_PRECISION,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
    )
