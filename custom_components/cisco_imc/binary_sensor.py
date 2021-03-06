"""Binary sensor platform for CiscoImc."""
import logging
from homeassistant.components.binary_sensor import DEVICE_CLASSES, BinarySensorEntity
from homeassistant.core import callback
from homeassistant.const import CONF_IP_ADDRESS

from .const import DOMAIN, NAME
from .imc_device import CiscoImcDevice
from .models import CiscoImcBinarySensorEntityDescription


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Tesla binary_sensors by config_entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    entities = []
    for device_key in entry_data["devices"]["binary_sensor"].keys():
        device_class = entry_data["devices"]["binary_sensor"][device_key]
        entities.append(CiscoImcBinarySensor(hass, config_entry, device_class, coordinator))
    async_add_entities(entities, True)


class CiscoImcBinarySensor(CiscoImcDevice, BinarySensorEntity):
    """Implement an Cisco IMC binary sensor for ...."""

    def __init__(self, hass, config_entry, entity_description, coordinator):
        """Initialise the binary_sensor."""
        self.hass = hass
        self.platform_name = "binary_sensor"
        self.entity_description = entity_description
        self.imc = config_entry.data.get(CONF_IP_ADDRESS)[0]
        self.coordinator = coordinator
        self._attr_name = f"{NAME} {self.imc} {self.entity_description.name}"
        if self.hass.custom_attributes[self.imc]['usr_lbl']:
            self._attr_name = f"{self.hass.custom_attributes[self.imc]['usr_lbl']} {self.entity_description.name}"        
        self._attributes = {}
        
        super().__init__(self, hass, self.imc, entity_description, coordinator)

    @property
    def unique_id(self):
        """Return a unique ID."""
        if not self.coordinator.imc:
            return None
        return f"{DOMAIN}_{self.imc.lower().replace('.', '_')}_{self.entity_description.key}"
        
    @property
    def device_class(self):
        """Return the class of this binary sensor."""
        return (
            self.entity_description.device_class
            if self.entity_description.device_class in DEVICE_CLASSES
            else None
        )

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self.coordinator.sensor_state(self.entity_description.key)
        
    @property
    def available(self):
        return True

    @callback
    def async_update_available(self):
        super().async_update_available()
        self._attr_extra_state_attributes["available"] = self._attr_available

