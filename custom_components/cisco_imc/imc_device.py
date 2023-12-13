"""Support for Cisco UCS server IMCs."""
from functools import wraps
import logging
from typing import Any, Optional

from homeassistant.const import ATTR_BATTERY_CHARGING, ATTR_BATTERY_LEVEL
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from imcsdk.imchandle import ImcHandle
from urllib.error import URLError

from .const import DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)


class CiscoImcDevice(CoordinatorEntity):
    """Representation of a Cisco IMC device."""

    class Decorators(CoordinatorEntity):
        """Decorators for Cisco IMC Devices."""

        @classmethod
        def check_for_reauth(cls, func):
            """Wrap a Cisco IMC device function to check for need to reauthenticate."""

            @wraps(func)
            async def wrapped(*args, **kwargs):
                result: Any = None
                self_object: Optional[Cisco_Imc_Device] = None
                if isinstance(args[0], Cisco_Imc_Device):
                    self_object = args[0]
                try:
                    result = await func(*args, **kwargs)
                except IncompleteCredentials:
                    if self_object and self_object.config_entry_id:
                        _LOGGER.debug(
                            "Reauth needed for %s after calling: %s",
                            self_object,
                            func,
                        )
                        await self_object.hass.config_entries.async_reload(
                            self_object.config_entry_id
                        )
                    return None
                return result

            return wrapped

    def __init__(self, upstream_entity, hass, imc, entity_description, coordinator):
        """Initialise the Cisco IMC device."""
        super().__init__(coordinator)
        self.upstream_entity = upstream_entity
        self.hass = hass
        self.imc = imc
        self.entity_description = entity_description
        self.coordinator = coordinator
        self.config_entry_id: Optional[str] = None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self.entity_description.icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return self._attributes

    @property
    def device_info(self):
        """Return the device_info of the device."""
        my_name = f"{NAME} {self.imc}"
        if self.hass.custom_attributes[self.imc]['usr_lbl']:
            my_name = self.hass.custom_attributes[self.imc]['usr_lbl']
        return {
            "identifiers": {(DOMAIN, self.imc)},
            "name": my_name,
            "manufacturer": "Cisco",
            "model": self.hass.custom_attributes[self.imc]['model'],
        }
