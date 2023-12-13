"""Sensor platform for CiscoImc."""

from __future__ import annotations

import logging

from typing import Any

from imcsdk.imchandle import ImcHandle

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import CONF_IP_ADDRESS


from .const import DOMAIN, NAME, SENSOR_TYPES, RACK_UNIT_SENSORS
from .imc_device import CiscoImcDevice
from .models import CiscoImcSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a IMC entry."""
    # Add the needed sensors to hass
    

    entry_data = hass.data[DOMAIN][entry.entry_id]
    platform_name = entry.title
    coordinator = entry_data["coordinator"]

    entities = []
    for device_key in entry_data["devices"]["sensor"].keys():
        device_class = entry_data["devices"]["sensor"][device_key]
        entities.append(CiscoImcRackUnitSensor(hass, entry, platform_name, device_class, coordinator))
    async_add_entities(entities, True)


class CiscoImcSensorEntity(CiscoImcDevice, SensorEntity):
    """Abstract class for a Cisco IMC sensor."""
    
    entity_description: CiscoImcSensorEntityDescription
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        platform_name:str,
        description: CiscoImcSensorEntityDescription,
        coordinator,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.platform_name = platform_name
        self.entity_description = description
        self.imc = config_entry.data.get(CONF_IP_ADDRESS)[0]
        self.coordinator = coordinator
        self._attr_name = f"{NAME} {self.imc} {self.entity_description.name}"
        if 'usr_lbl' in self.hass.custom_attributes[self.imc]:
            if self.hass.custom_attributes[self.imc]['usr_lbl']:
                self._attr_name = f"{self.hass.custom_attributes[self.imc]['usr_lbl']} {self.entity_description.name}"        
        self._attributes = {}
        super().__init__(self, hass, self.imc, description, coordinator)
        
    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        if not self.coordinator.imc:
            return None
        return f"{DOMAIN}_{self.imc.lower().replace('.', '_')}_{self.entity_description.key}"
        
class CiscoImcRackUnitSensor(CiscoImcSensorEntity):
    """Representation of a Cisco IMC Rack Unit sensor."""
    
    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
#        if self.coordinator.sensor_state(self.entity_description.key) is None:
#            return None
        return self.hass.custom_attributes[self.imc][self.entity_description.key]
        
    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self.hass.custom_attributes[self.imc][self.entity_description.key]
