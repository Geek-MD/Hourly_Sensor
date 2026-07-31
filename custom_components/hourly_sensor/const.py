"""Constants for Hourly Sensor."""

from typing import Final

DOMAIN: Final = "hourly_sensor"

CONF_AGGREGATION: Final = "aggregation"
CONF_HOURS: Final = "hours"
CONF_NAME: Final = "name"
CONF_PRECISION: Final = "precision"
CONF_SOURCE_ENTITY: Final = "source_entity"

AGGREGATION_CHANGE: Final = "change"
AGGREGATION_SUM: Final = "sum"
AGGREGATION_AVERAGE: Final = "average"
AGGREGATION_MINIMUM: Final = "minimum"
AGGREGATION_MAXIMUM: Final = "maximum"
AGGREGATION_LAST: Final = "last"

AGGREGATIONS: Final = (
    AGGREGATION_CHANGE,
    AGGREGATION_SUM,
    AGGREGATION_AVERAGE,
    AGGREGATION_MINIMUM,
    AGGREGATION_MAXIMUM,
    AGGREGATION_LAST,
)

DEFAULT_AGGREGATION: Final = AGGREGATION_CHANGE
DEFAULT_HOURS: Final = 1
DEFAULT_PRECISION: Final = 2
MIN_HOURS: Final = 1
MAX_HOURS: Final = 168
MIN_PRECISION: Final = 0
MAX_PRECISION: Final = 6

PLATFORMS: Final = ("sensor",)
