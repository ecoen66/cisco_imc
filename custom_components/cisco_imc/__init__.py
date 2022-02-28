"""
Custom integration to integrate Cisco UCS IMC with Home Assistant.

For more details about this integration, please refer to
https://github.com/ecoen66/cisco_imc
"""
from __future__ import annotations
import asyncio
import logging
from datetime import timedelta
from collections import defaultdict
#from typing import List

from imcsdk.imchandle import ImcHandle
from imcsdk.imcexception import ImcLoginError, ImcException, ImcConnectionError

from urllib.error import URLError

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.config_entries import ConfigEntry, SOURCE_REAUTH, SOURCE_IMPORT
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.entity_registry as er

from .services import async_setup_services, async_unload_services
from .switch import ImcPollingSwitch
from .binary_sensor import CiscoImcBinarySensor
from .sensor import CiscoImcRackUnitSensor
from .imc_device import CiscoImcDevice

from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    CONF_IP_ADDRESS,
    CONF_USERNAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_CLOSE,
)
from .const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    DATA_API_CLIENT,
    DATA_LISTENER,
    RACK_UNIT_UPDATE_DELAY,
    RACK_UNIT_SENSORS,
    SWITCH,
    BINARY_SENSOR,
    SENSOR_TYPES,
    SWITCH_TYPE,
    BINARY_SENSOR_TYPE,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)

_LOGGER = logging.getLogger(__name__)


@callback
def _async_configured_ips(hass):
    """Return a set of configured IMCs."""
    _LOGGER.debug("Creating a list of configured IMCs")
    return {
        entry.data[CONF_IP_ADDRESS]
        for entry in hass.config_entries.async_entries(DOMAIN)
        if CONF_IP_ADDRESS in entry.data
    }


async def async_setup(_hass: HomeAssistant, _config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info(STARTUP_MESSAGE)

    imc = config_entry.title
    if not hass.data[DOMAIN]:
        _LOGGER.debug(f"{imc} Calling setup services")
        await async_setup_services(hass)
        _LOGGER.debug(f"{imc} Returned from setup services")
    if imc in hass.data[DOMAIN] and CONF_SCAN_INTERVAL in hass.data[DOMAIN][imc]:
        _LOGGER.debug(f"{imc} imc found in hass.data[DOMAIN]")
        scan_interval = hass.data[DOMAIN][imc][CONF_SCAN_INTERVAL]
        hass.config_entries.async_update_entry(
            config_entry, options={CONF_SCAN_INTERVAL: scan_interval}
        )
        hass.data[DOMAIN].pop(imc)
    try:
        _LOGGER.debug(f"{imc} Setting up coordinator")
        coordinator = CiscoImcDataService(hass, config_entry)
        _LOGGER.debug(f"{imc} Asking coordinator to login")
        await coordinator.async_login()
        _LOGGER.debug("Logged in to imc %s in __init__.py", imc)

    except URLError as ex:
        raise ConfigEntryAuthFailed(ex) from ex
    except Exception as ex:
        raise ConfigEntryNotReady(ex) from ex

    async def _async_close_client(*_):
        await coordinator.async_close()

    @callback
    def _async_create_close_task():
        asyncio.create_task(_async_close_client())

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_CLOSE, _async_close_client)
    )
    config_entry.async_on_unload(_async_create_close_task)

    # Fetch initial data so we have data when entities subscribe
    entry_data = hass.data[DOMAIN][config_entry.entry_id] = {
        "coordinator": coordinator,
        "devices": dict[
            str,
            dict[
                str,
                type [CiscoImcDevice]
            ]
        ],
        DATA_LISTENER: [config_entry.add_update_listener(update_listener)],
    }
    _LOGGER.debug(f"{imc} await coordinator.async_config_entry_first_refresh()")
    await coordinator.async_config_entry_first_refresh()

    all_devices: dict[
        str,
        dict[
            str,
            type [CiscoImcDevice]
        ],
    ] = await get_homeassistant_components(hass, config_entry)

    if not all_devices:
        return False
    entry_data["devices"] = all_devices.copy()

    _LOGGER.debug(f"{imc} devices = {entry_data['devices']}")

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)
    
#    entity_registry = er.async_get(hass)
#    attrs: Dict[str, Any] = {ATTR_RESTORED: True}

#                states.async_set(entry.entity_id, STATE_UNAVAILABLE, attrs)

#    print(f'{}')

    return True

async def get_homeassistant_components(hass, config_entry) -> dict[
        str,
        dict[
            str,
            type [CiscoImcDevice]
        ],
    ]:
    """Return a list of home assistant components for the IMC."""
    platform_name = config_entry.title    
    services: dict[
        str,
        dict[
            str,
            type [CiscoImcDevice]
        ],
    ] = {}
    
    services.setdefault("sensor", {})
    services.setdefault("switch", {})
    services.setdefault("binary_sensor", {})
    for key in RACK_UNIT_SENSORS:
        for sensor_type in SENSOR_TYPES:
            if sensor_type.key == key:
                services["sensor"][key] = sensor_type
    
    services["switch"][SWITCH] = SWITCH_TYPE
    services["binary_sensor"][BINARY_SENSOR] = BINARY_SENSOR_TYPE
    return services

async def async_unload_entry(hass, config_entry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    await hass.data[DOMAIN].get(config_entry.entry_id)[
        "coordinator"
    ].async_close()
    for listener in hass.data[DOMAIN][config_entry.entry_id][DATA_LISTENER]:
        listener()
    imc = config_entry.title
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
        _LOGGER.debug("Unloaded entry for %s", imc)
        if not hass.data[DOMAIN]:
            async_unload_services(hass)
        return True
    return False


async def update_listener(hass, config_entry):
    """Update when config_entry options update."""
    imc = config_entry.title
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    old_update_interval = coordinator.update_interval
    coordinator.update_interval = config_entry.options.get(CONF_SCAN_INTERVAL)
    if old_update_interval != coordinator.update_interval:
        _LOGGER.debug(
            "Changing scan_interval for %s from %s to %s",
            imc,
            old_update_interval,
            coordinator.update_interval,
        )

class CiscoImcDataService(DataUpdateCoordinator):
    """This class handle communication and stores the data."""

    def __init__(self, hass, config_entry):
        """Initialize the class."""
        self.hass = hass
        self.config_entry = config_entry
        self.imc = config_entry.data.get(CONF_IP_ADDRESS)[0]
        self.username = self.config_entry.data.get(CONF_USERNAME)[0]
        self.password = self.config_entry.data.get(CONF_PASSWORD)
        _LOGGER.debug("about to setdefault custom_attributes for %s", self.imc)
        if not hasattr(self.hass, 'custom_attributes'):
            self.hass.custom_attributes = {}
        _LOGGER.debug("about to setdefault custom_attributes.imc for %s", self.imc)
        self.hass.custom_attributes.setdefault(self.imc, {})
        _LOGGER.debug("about to set custom_attributes for %s", self.imc)
        self.hass.custom_attributes[self.imc] = {}
        _LOGGER.debug("about to set polling_switch for %s", self.imc)
        self.hass.custom_attributes[self.imc]['polling_switch'] = True
#        self.hass.data[DOMAIN][config_entry.entry_id]['devices']['switch'][SWITCH]._is_on = True
        self.hass.custom_attributes[self.imc]['reachable'] = False
        self.hass.custom_attributes[self.imc]['unreachable_counter'] = 0
        self.update_interval = timedelta(seconds=MIN_SCAN_INTERVAL)
        self.client = ImcHandle(
            self.imc,
            self.username,
            self.password,
            secure=True,
            auto_refresh=True,
            force=True,
            timeout=60,
        )        
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=self.update_interval)   
                     
    async def async_login(self):
        response = False
        self.hass.custom_attributes[self.imc]['reachable'] = False
        try:
            _LOGGER.debug(f"{self.imc} Logging in from CiscoImcDataService")
            response = await self.hass.async_add_executor_job(self.client.login)
        except URLError as ex:
            self.hass.custom_attributes[self.imc]['reachable'] = False
            self.hass.custom_attributes[self.imc]['unreachable_counter'] += 1
            raise UpdateFailed("Unable to contact the IMC, skipping update") from ex
#            _LOGGER.debug(f"{self.imc} Unable to contact the IMC, skipping update")
#            return False
        except ImcLoginError as ex:
            _LOGGER.error("Could not login to the IMC %s", self.imc)
            raise ConfigEntryAuthFailed from ex
        except ImcException as ex:
            _LOGGER.error("Exception logging in to the IMC %s", self.imc)
            raise ConfigEntryNotReady from ex
        _LOGGER.debug(f"{self.imc} Login from CiscoImcDataService = {response}")
        self.hass.custom_attributes[self.imc]['reachable'] = response
        _LOGGER.debug(f"{self.imc} Reachable set to {self.hass.custom_attributes[self.imc]['reachable']}")
        return response
        
    async def async_close(self):
        response = await self.hass.async_add_executor_job(self.client.logout)
        self.hass.custom_attributes[self.imc]['reachable'] = False
        _LOGGER.debug(f"{self.imc} Logout from CiscoImcDataService = {response}")
        return response
        
    async def _async_update_data(self):
        """Update data."""
        _LOGGER.debug(f"{self.imc} polling_switch = {self.hass.custom_attributes[self.imc]['polling_switch']}")
        if self.hass.custom_attributes[self.imc]['polling_switch']:
            _LOGGER.debug(f"{self.imc} reachable = {self.hass.custom_attributes[self.imc]['reachable']}")
            if not self.hass.custom_attributes[self.imc]['reachable']:
                result = await self.async_login()
                if not result:
                    self.hass.custom_attributes[self.imc]['unreachable_counter'] += 1
                    return False
            await self.hass.async_add_executor_job(self.update)
            
        
    def update(self):
        """Update the data from the Cisco IMC API."""
        try:
            rack_unit = self.client.query_dn("sys/rack-unit-1")
        except URLError as ex:
            self.hass.custom_attributes[self.imc]['reachable'] = False
            self.hass.custom_attributes[self.imc]['unreachable_counter'] += 1
            raise UpdateFailed("Unable to contact the IMC, skipping update") from ex
        except Exception as ex:
            self.hass.custom_attributes[self.imc]['reachable'] = False
            self.hass.custom_attributes[self.imc]['unreachable_counter'] += 1
            raise UpdateFailed("Unable to contact the IMC, skipping update") from ex
        self.hass.custom_attributes[self.imc].clear()
        self.hass.custom_attributes[self.imc]['reachable'] = True
        self.hass.custom_attributes[self.imc]['polling_switch'] = True
        self.hass.custom_attributes[self.imc]['unreachable_counter'] = 0

        for key, value in rack_unit.__dict__.items():
            if key in RACK_UNIT_SENSORS:
                self.hass.custom_attributes[self.imc][key] = value
        _LOGGER.debug(f"Updated Cisco IMC Rack Unit {self.imc}: {self.hass.custom_attributes[self.imc]}")

    def set_polling_state(self, new_state):
        """Update the polling status the Cisco IMC API."""
        self.hass.custom_attributes[self.imc]['polling_switch'] = new_state
        _LOGGER.debug(f"Updated Cisco IMC Polling {self.imc}: %s", self.hass.custom_attributes[self.imc]['polling_switch'])

    def is_polling(self):
        """Return the polling status the Cisco IMC API."""
        is_polling = self.hass.custom_attributes[self.imc]['polling_switch'] == True
        _LOGGER.debug(f"Cisco IMC Polling {self.imc}: %s", is_polling)
        return is_polling

    def sensor_state(self, key):
        """Return the state of a Cisco IMC sensor."""
        return self.hass.custom_attributes[self.imc][key]
