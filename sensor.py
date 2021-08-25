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
    TEMP_CELSIUS, LENGTH_CENTIMETERS, LENGTH_METERS, PERCENTAGE)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

# import homeassistant.config as config

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = '/dev/ttyUSB0'

CONF_PORT = "serial_port"
CONF_HEIGHT = "height"
CONF_OFFSET = "offset"

# Helper classes for declaring sensor configurations

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
        self.height = height
        self.offset = offset



PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_HEIGHT): cv.int,
    vol.Required(CONF_OFFSET): cv.int
})


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType,
                               async_add_entities, discovery_info=None):
    """Set up the WUnderground sensor."""
    port = config.get(CONF_PORT, DEFAULT_PORT)
    height = config.get(CONF_HEIGHT)
    offset = config.get(CONF_OFFSET)

    ecometers = EcoMeterS(port, height, offset, data_received)

    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(WUndergroundSensor(hass, rest, variable,
                                          unique_id_base))

    await rest.async_update()
    if not rest.data:
        raise PlatformNotReady

    async_add_entities(sensors, True)

def data_received(ecometer: EcoMeterS):


class EcoMeterSSensor(Entity):
    """Implementing the Eco Meter S sensor."""

    def __init__(self, hass: HomeAssistantType, rest, condition,
                 unique_id_base: str):
        """Initialize the sensor."""
        self.rest = rest
        self._condition = condition
        self._state = None
        self._attributes = {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }
        self._icon = None
        self._entity_picture = None
        self._unit_of_measurement = self._cfg_expand("unit_of_measurement")
        self.rest.request_feature(SENSOR_TYPES[condition].feature)
        # This is only the suggested entity id, it might get changed by
        # the entity registry later.
        self.entity_id = sensor.ENTITY_ID_FORMAT.format('wupws_' + condition)
        self._unique_id = "{},{}".format(unique_id_base, condition)
        self._device_class = self._cfg_expand("device_class")

    def _cfg_expand(self, what, default=None):
        """Parse and return sensor data."""
        cfg = SENSOR_TYPES[self._condition]
        val = getattr(cfg, what)
        if not callable(val):
            return val
        try:
            val = val(self.rest)
        except (KeyError, IndexError, TypeError, ValueError) as err:
            _LOGGER.warning("Failed to expand cfg from WU API."
                            " Condition: %s Attr: %s Error: %s",
                            self._condition, what, repr(err))
            val = default

        return val

    def _update_attrs(self):
        """Parse and update device state attributes."""
        attrs = self._cfg_expand("device_state_attributes", {})

        for (attr, callback) in attrs.items():
            if callable(callback):
                try:
                    self._attributes[attr] = callback(self.rest)
                except (KeyError, IndexError, TypeError, ValueError) as err:
                    _LOGGER.warning("Failed to update attrs from WU API."
                                    " Condition: %s Attr: %s Error: %s",
                                    self._condition, attr, repr(err))
            else:
                self._attributes[attr] = callback

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._cfg_expand("friendly_name")

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return icon."""
        return self._icon

    @property
    def entity_picture(self):
        """Return the entity picture."""
        return self._entity_picture

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the units of measurement."""
        return self._device_class

    async def async_update(self):
        """Update current conditions."""
        await self.rest.async_update()

        if not self.rest.data:
            # no data, return
            return

        self._state = self._cfg_expand("value")
        self._update_attrs()
        self._icon = self._cfg_expand("icon", super().icon)
        url = self._cfg_expand("entity_picture")
        if isinstance(url, str):
            self._entity_picture = re.sub(r'^http://', 'https://',
                                          url, flags=re.IGNORECASE)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id


class WUndergroundData:
    """Get data from WUnderground."""

    def __init__(self, hass, api_key, pws_id, numeric_precision, unit_system_api, unit_system, lang, latitude,
                 longitude):
        """Initialize the data object."""
        self._hass = hass
        self._api_key = api_key
        self._pws_id = pws_id
        self._numeric_precision = numeric_precision
        self._unit_system_api = unit_system_api
        self.unit_system = unit_system
        self.units_of_measurement = None
        self._lang = 'language={}'.format(lang)
        self._latitude = latitude
        self._longitude = longitude
        self._features = set()
        self.data = None
        self._session = async_get_clientsession(self._hass)

        if unit_system_api == 'm':
            self.units_of_measurement = (TEMP_CELSIUS, LENGTH_MILLIMETERS, LENGTH_METERS, SPEED_KILOMETERS_PER_HOUR,
                                         PRESSURE_MBAR, PRECIPITATION_MILLIMETERS_PER_HOUR, PERCENTAGE)
        else:
            self.units_of_measurement = (TEMP_FAHRENHEIT, LENGTH_INCHES, LENGTH_FEET, SPEED_MILES_PER_HOUR,
                                         PRESSURE_INHG, PRECIPITATION_INCHES_PER_HOUR, PERCENTAGE)

    def request_feature(self, feature):
        """Register feature to be fetched from WU API."""
        self._features.add(feature)

    def _build_url(self, baseurl):
        if baseurl is _RESOURCECURRENT:
            if self._numeric_precision == 'none':
                url = baseurl.format(self._pws_id, self._unit_system_api, self._api_key)
            else:
                url = baseurl.format(self._pws_id, self._unit_system_api, self._api_key) + '&numericPrecision=decimal'
        else:
            url = baseurl.format(self._latitude, self._longitude, self._unit_system_api, self._lang, self._api_key)

        return url

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data from WUnderground."""
        headers = {'Accept-Encoding': 'gzip'}
        try:
            with async_timeout.timeout(10, loop=self._hass.loop):
                response = await self._session.get(self._build_url(_RESOURCECURRENT), headers=headers)
            result_current = await response.json()

            # need to check specific new api errors
            # if "error" in result['response']:
            #     raise ValueError(result['response']["error"]["description"])
            # _LOGGER.debug('result_current' + str(result_current))

            if result_current is None:
                raise ValueError('NO CURRENT RESULT')
            with async_timeout.timeout(10, loop=self._hass.loop):
                response = await self._session.get(self._build_url(_RESOURCEFORECAST), headers=headers)
            result_forecast = await response.json()

            if result_forecast is None:
                raise ValueError('NO FORECAST RESULT')

            result = {**result_current, **result_forecast}

            self.data = result
        except ValueError as err:
            _LOGGER.error("Check WUnderground API %s", err.args)
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Error fetching WUnderground data: %s", repr(err))
