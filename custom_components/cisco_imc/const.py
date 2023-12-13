"""Constants for CiscoImc."""
from enum import Enum
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass

from .models import (
    CiscoImcBinarySensorEntityDescription,
    CiscoImcSensorEntityDescription,
    CiscoImcSwitchEntityDescription,
)

# Base component constants
NAME = "Cisco IMC"
DOMAIN = "cisco_imc"
VERSION = "v2.3.0"

ISSUE_URL = "https://github.com/ecoen66/cisco_imc/issues"

LOGGER = logging.getLogger(__package__)

DATA_API_CLIENT = "api_client"

RACK_UNIT_UPDATE_DELAY = timedelta(minutes=1)

DATA_LISTENER = "listener"
ICONS = {
    "model": "mdi:card-text-outline",
    "serial": "mdi:numeric",
    "asset_tag": "mdi:tag-outline",
    "usr_lbl": "mdi:label-outline",
    "uuid": "mdi:sticker-text-outline",
    "num_of_cpus": "mdi:cpu-64-bit",
    "num_of_cores": "mdi:checkbox-multiple-blank-outline",
    "num_of_threads": "mdi:math-norm",
    "total_memory": "mdi:memory",
    "cimc_reset_reason": "mdi:alert-octagon-outline",
    "oper_power": "mdi:power",
    "reachable": "mdi:lan-connect",
    "polling_switch": "mdi:sync",
    "ip_address": "mdi:ip-outline",
}
DEFAULT_SCAN_INTERVAL = 660
MIN_SCAN_INTERVAL = 60

SIGNAL_STATE_UPDATED = f"{DOMAIN}.updated"

# Platforms
PLATFORMS = ["binary_sensor", "sensor", "switch"]

# Configuration and options
CONF_NAME = "name"

RACK_UNIT_SENSORS = [
    "model",
    "serial",
    "asset_tag",
    "usr_lbl",
    "uuid",
    "num_of_cpus",
    "num_of_cores",
    "num_of_threads",
    "total_memory",
    "cimc_reset_reason",
    "oper_power"
]

STATIC_SENSOR = "ip_address"
SWITCH = "polling_switch"
BINARY_SENSOR = "reachable"

POLLING_ICON = "mdi:sync"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

CISCO_IMC_SERVICES = "cisco_imc_services"
SERVICE_DESIRED_STATE = "desired_state"
SERVICE_ENTITY_TYPE = "entity_type"
SERVICE_ENTITY_ID = "entity_id"
SERVICE_ENTRY_ID = "config_entry_id"
SERVICE_DATA = "data"
SERVICE_SET_ADMIN_POWER = "set_admin_power"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
SENSOR_TYPES = [
    CiscoImcSensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:card-text-outline",
    ),
    CiscoImcSensorEntityDescription(
        key="serial",
        name="Serial",
        icon="mdi:numeric",
    ),
    CiscoImcSensorEntityDescription(
        key="asset_tag",
        name="Asset Tag",
        icon="mdi:tag-outline",
    ),
    CiscoImcSensorEntityDescription(
        key="usr_lbl",
        name="User Label",
        icon="mdi:label-outline",
    ),
    CiscoImcSensorEntityDescription(
        key="uuid",
        name="UUID",
        icon="mdi:sticker-text-outline",
    ),
    CiscoImcSensorEntityDescription(
        key="num_of_cpus",
        name="CPUs",
        icon="mdi:cpu-64-bit",
    ),
    CiscoImcSensorEntityDescription(
        key="num_of_cores",
        name="Cores",
        icon="mdi:checkbox-multiple-blank-outline",
    ),
    CiscoImcSensorEntityDescription(
        key="num_of_threads",
        name="Threads",
        icon="mdi:math-norm",
    ),
    CiscoImcSensorEntityDescription(
        key="total_memory",
        name="Total Memory",
        icon="mdi:memory",
        unit_of_measurement="MB",
    ),
    CiscoImcSensorEntityDescription(
        key="cimc_reset_reason",
        name="Reset Reason",
        icon="mdi:alert-octagon-outline",
    ),
    CiscoImcSensorEntityDescription(
        key="oper_power",
        name="Power",
        icon="mdi:power",
    ),
]

STATIC_SENSOR_TYPE = CiscoImcSensorEntityDescription(
    key="ip_address",
    name="IP Address",
    icon="mdi:ip-outline",
)

BINARY_SENSOR_TYPE = CiscoImcBinarySensorEntityDescription(
    key="reachable",
    name="Reachable",
    icon="mdi:lan-connect",
    device_class=BinarySensorDeviceClass.CONNECTIVITY
)

SWITCH_TYPE = CiscoImcSwitchEntityDescription(
    key="polling_switch",
    name="Polling Switch",
    icon="mdi:sync",
    device_class=SwitchDeviceClass.SWITCH
)