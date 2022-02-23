"""Switch platform for CiscoImc."""

import logging

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.const import CONF_IP_ADDRESS

from .const import DOMAIN, NAME
from .imc_device import CiscoImcDevice
from .models import CiscoImcSwitchEntityDescription


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the IMC switches by config_entry."""
    print(f"entry_id = {config_entry.entry_id}")
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    entities = []
    for device_key in entry_data["devices"]["switch"].keys():
        device_class = entry_data["devices"]["switch"][device_key]
        entities.append(ImcPollingSwitch(hass, config_entry, device_class, coordinator))
    async_add_entities(entities, True)



class ImcPollingSwitch(CiscoImcDevice, SwitchEntity):
    """Representation of an IMC polling switch."""

    entity_description: CiscoImcSwitchEntityDescription

    def __init__(self, hass, config_entry, entity_description, coordinator):
        """Initialise the switch."""
        self.hass = hass
        self.platform_name = "switch"
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

    async def async_turn_on(self, **kwargs):
        """Send the on command."""
        _LOGGER.debug("Enable polling for: %s", self.name)
        self.coordinator.set_polling_state(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Send the off command."""
        _LOGGER.debug("Disable polling for: %s", self.name)
        self.coordinator.set_polling_state(False)
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Get whether the switch is in on state."""
        if self.coordinator.is_polling() is None:
            return None
        return self.coordinator.is_polling()

    @property
    def available(self):
        return True

    @callback
    def async_update_available(self):
        super().async_update_available()
        self._attr_extra_state_attributes["available"] = self._attr_available


