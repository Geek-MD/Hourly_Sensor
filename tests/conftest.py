"""Test configuration that isolates the pure aggregation model."""

import sys
from pathlib import Path
from types import ModuleType

PACKAGE = "custom_components.hourly_sensor"

package = ModuleType(PACKAGE)
package.__path__ = [
    str(Path(__file__).parents[1] / "custom_components" / "hourly_sensor")
]
package.HourlySensorConfigEntry = object
sys.modules[PACKAGE] = package
