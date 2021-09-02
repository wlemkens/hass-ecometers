"""
Support for WUndergroundPWS weather service.

For more details about this platform, please refer to the documentation at
https://github.com/cytech/Home-Assistant-wundergroundpws
"""
import asyncio
from datetime import timedelta
import logging
import re

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.components import sensor
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    TEMP_CELSIUS, LENGTH_CENTIMETERS, LENGTH_METERS, PERCENTAGE, VOLUME_LITERS)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

from .ecometers.ecometers.ecometers import EcoMeterS
# import homeassistant.config as config

from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

DEFAULT_PORT = '/dev/ttyUSB0'
 
CONF_PORT = "serial_port"
CONF_HEIGHT = "height"
CONF_OFFSET = "offset"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_HEIGHT): cv.positive_int,
    vol.Required(CONF_OFFSET): cv.positive_int
})

_LOGGER = logging.getLogger(__name__)

class EcoMeterSSensorConfig:
    """
    Eco Meter S Sensor Configuration.
    """

    def __init__(self, friendly_name, port, height, offset):
        """Constructor.
        Args:
            friendly_name (string|func): Friendly name
            port (string): serial port
            height (int): height of the tank in cm
            offset (int): offset of the sensor in cm
        """
        self.friendly_name = friendly_name
        self.port = port
        self.height = height
        self.offset = offset


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    port = config.get(CONF_PORT, DEFAULT_PORT)
    height = config.get(CONF_HEIGHT)
    offset = config.get(CONF_OFFSET)
#    _LOGGER.info("Config, port = %s, heigt = %d, offset = %d",
#                            port, height, offset)


    ecometers = EcoMeterS(port, height, offset)

    sensors = []
    sensors.append(EcoMeterSLevelSensor(ecometers, "eco_meter_s"))
    sensors.append(EcoMeterSUsableSensor(ecometers, "eco_meter_s"))
    sensors.append(EcoMeterSPercentageSensor(ecometers, "eco_meter_s"))
    sensors.append(EcoMeterSTemperatureSensor(ecometers, "eco_meter_s"))

    add_entities(sensors, True)
    #add_entities([ExampleSensor()])


class EcoMeterSSensor(Entity):
    """Implementing the Eco Meter S sensor."""

    def __init__(self, ecometers: EcoMeterS,
                 unique_id_base: str):
        """Initialize the sensor."""
        self.ecometers = ecometers
        self.ecometers.add_on_data_received_callback(self.on_data_received)
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return icon."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement
    
    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    def on_data_received(self, ecometers: EcoMeterS):
        _LOGGER.warning("Data received base")

class EcoMeterSLevelSensor(EcoMeterSSensor):
    def __init__(self, ecometers: EcoMeterS,
                unique_id_base: str):
        super(EcoMeterSLevelSensor, self).__init__(ecometers, unique_id_base)
        self._name = "Tank level"
        self._unit_of_measurement = LENGTH_CENTIMETERS
        self._icon = "mdi:arrow-expand-vertical"
        self._unique_id = "{:}_{:}".format(unique_id_base,"level")
        self._state = ecometers.level

    def on_data_received(self, ecometers: EcoMeterS):
        self._state = ecometers.level


class EcoMeterSUsableSensor(EcoMeterSSensor):
    def __init__(self, ecometers: EcoMeterS,
                unique_id_base: str):
        super(EcoMeterSUsableSensor, self).__init__(ecometers, unique_id_base)
        self._name = "Tank volume"
        self._unit_of_measurement = VOLUME_LITERS
        self._icon = "mdi:hydraulic-oil-level"
        self._unique_id = "{:}_{:}".format(unique_id_base,"volume")
        self._state = ecometers.usable

    def on_data_received(self, ecometers: EcoMeterS):
        self._state = ecometers.usable


class EcoMeterSPercentageSensor(EcoMeterSSensor):
    def __init__(self, ecometers: EcoMeterS,
                unique_id_base: str):
        super(EcoMeterSPercentageSensor, self).__init__(ecometers, unique_id_base)
        self._name = "Tank fill"
        self._unit_of_measurement = PERCENTAGE
        self._icon = "mdi:hydraulic-oil-level"
        self._unique_id = "{:}_{:}".format(unique_id_base,"percentage")
        self._state = ecometers.percentage

    def on_data_received(self, ecometers: EcoMeterS):
        self._state = ecometers.percentage

class EcoMeterSTemperatureSensor(EcoMeterSSensor):
    def __init__(self, ecometers: EcoMeterS,
                unique_id_base: str):
        super(EcoMeterSTemperatureSensor, self).__init__(ecometers, unique_id_base)
        self._name = "Tank temperature"
        self._unit_of_measurement = TEMP_CELSIUS
        self._icon = "mdi:thermometer-lines"
        self._unique_id = "{:}_{:}".format(unique_id_base,"temperature")
        self._state = ecometers.temperature

    def on_data_received(self, ecometers: EcoMeterS):
        self._state = ecometers.temperature

