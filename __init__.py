"""
Eco Meter S component

Configuration:

"""
from homeassistant.core import callback
from ecometers.ecometers.ecometers import EcoMeterS

import voluptuous as vol

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "eco_meter_s"

DEFAULT_PORT = '/dev/ttyUSB0'

CONF_PORT = "serial_port"
CONF_HEIGHT = "height"
CONF_OFFSET = "offset"

# Schema to validate the configured MQTT topic
CONFIG_SCHEMA = vol.Schema({
    (CONF_PORT): str,
    (CONF_HEIGHT): int,
    (CONF_OFFSET): int,
})


async def async_setup(hass, config):
    """Set up the MQTT async example component."""
    serial_port = config[DOMAIN][CONF_PORT]
    height = config[DOMAIN][CONF_HEIGHT]
    offset = config[DOMAIN][CONF_OFFSET]

    ecometers = EcoMeterS(serial_port, height, offset, data_received)

    temperature_id = "tank_temperature"
    distance_id = "tank_distance"
    level_id = "tank_level"
    volume_id = "tank_volume"
    percentage_id = "tank_percentage"

    # Listen to a message on MQTT.
    @callback
    def data_received():
        """A new MQTT message has been received."""
        print(ecometers.temperature)
        print(ecometers.distance)
        hass.states.async_set(temperature_id, ecometers.temperature)
        hass.states.async_set(distance_id, ecometers.distance)
        hass.states.async_set(level_id, ecometers.level)
        hass.states.async_set(volume_id, ecometers.volume)
        hass.states.async_set(percentage_id, ecometers.precentage)

    # Return boolean to indicate that initialization was successfully.
    return True
