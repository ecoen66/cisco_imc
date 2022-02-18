"""Constants for imc_monitor tests."""
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_USERNAME,
    CONF_PASSWORD,
)

# Mock config data to be used across multiple tests
MOCK_CONFIG = {CONF_IP_ADDRESS: "192.168.1.1", CONF_USERNAME: "test_username", CONF_PASSWORD: "test_password"}