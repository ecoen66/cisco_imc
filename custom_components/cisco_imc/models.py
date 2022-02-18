"""Models for the CiscoIMC integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription


@dataclass
class CiscoImcSensorEntityDescription(SensorEntityDescription):
    """Sensor entity description for CiscoImc."""

    property_key: str | None = None

@dataclass
class CiscoImcBinarySensorEntityDescription(BinarySensorEntityDescription):
    """BinarySensor entity description for CiscoImc."""

    property_key: str | None = None

@dataclass
class CiscoImcSwitchEntityDescription(SwitchEntityDescription):
    """Switch entity description for CiscoImc."""

    property_key: str | None = None