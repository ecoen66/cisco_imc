"""Adds config flow for CiscoImc."""
from __future__ import annotations
import logging
from typing import Any
from collections import OrderedDict

import voluptuous as vol
from imcsdk.imchandle import ImcHandle
from imcsdk.imcexception import ImcLoginError, ImcException

from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    CONF_IP_ADDRESS,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
#from homeassistant.util import slugify

from .const import (
    DOMAIN,
    NAME,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    DATA_LISTENER,
    RACK_UNIT_SENSORS,
)

_LOGGER = logging.getLogger(__name__)



class CiscoImcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for CiscoImc."""

    VERSION = 1
    
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self.imc = None
        self.reauth = False

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
        ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        _LOGGER.debug("Step user")

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
#        if self._async_current_entries():
#            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            existing_entry = self._async_entry_for_imc(user_input[CONF_IP_ADDRESS])
            if existing_entry and not self.reauth:
                return self.async_abort(reason="already_configured")

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"

            if not errors:
                if existing_entry:
                    self.hass.config_entries.async_update_entry(
                        existing_entry, data=info
                    )
                    await self.hass.config_entries.async_reload(existing_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

                self.imc = user_input[CONF_IP_ADDRESS]
                return self.async_create_entry(title=self.imc, data=info)

        return self.async_show_form(
            step_id="user",
            data_schema=self._async_schema(),
            errors=errors,
            description_placeholders={},
        )

    async def async_step_reauth(self, data):
        """Handle configuration by re-auth."""
        self.imc = data[CONF_IP_ADDRESS]
        self.reauth = True
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    @callback
    def _async_schema(self):
        """Fetch schema with defaults."""
        _LOGGER.debug("config form schema")
        return vol.Schema(
            {
                vol.Required(CONF_IP_ADDRESS, default=self.imc): str,
                vol.Required(CONF_USERNAME, default=""): str,
                vol.Required(CONF_PASSWORD, default=""): str,

            }
        )

    @callback
    def _async_entry_for_imc(self, imc):
        """Find an existing entry for an IP Address."""
        for entry in self._async_current_entries():
            if entry.data.get(CONF_IP_ADDRESS) == imc:
                return entry
        return None


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for IMC."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(cv.positive_int, vol.Clamp(min=MIN_SCAN_INTERVAL)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    config = {}

    client = ImcHandle(
        data[CONF_IP_ADDRESS],
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        secure=True,
        auto_refresh=True,
        force=True,
        timeout=60
    )
    _LOGGER.debug("Parms passed to client in config flow: %s %s %s",data[CONF_IP_ADDRESS],data[CONF_USERNAME],data[CONF_PASSWORD])

    def system_info():
        response = client.login()
        _LOGGER.debug(f"Login in system_info = {response}")
        """Get system information from CiscoImc."""
        rack_unit = client.query_dn("sys/rack-unit-1")
        for key, value in rack_unit.__dict__.items():
            if key in RACK_UNIT_SENSORS:
                _LOGGER.debug(f"{key}: {value}")
    
    def system_logout():
        response = client.logout()    
        _LOGGER.debug(f"Logout in system_logout = {response}")

    try:
        await hass.async_add_executor_job(system_info)
        config[CONF_IP_ADDRESS] = data[CONF_IP_ADDRESS],
        config[CONF_USERNAME] = data[CONF_USERNAME],
        config[CONF_PASSWORD] = data[CONF_PASSWORD]

    except ImcLoginError as ex:
        _LOGGER.error("Authentication error: %s %s", ex.description, ex)
        raise InvalidAuth() from ex
    except ImcException as ex:
        _LOGGER.error("Unable to communicate with Cisco IMC API: %s", ex)
        raise CannotConnect() from ex
    finally:
        await hass.async_add_executor_job(system_logout)
    _LOGGER.debug("Credentials successfully connected to the Cisco IMC API")

    return config


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
        
