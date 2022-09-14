# hass-ecometers
Integration for the Eco Meter S tank level sensor

## Installation
This guide assumes your are in a terminal on the device running Home Assistant. 
Either directly or by ssh.

### Summary
- Put the component in the custom_components directory
- Add the component to the configuration.yaml
- Restart Home Assistant

### Component
The component needs to be installed in the `custom_components` directory.
This directory is located in the `config` directory that can be on different places depending on your Home Assistant setup.

 - HAOS : `/config`
 - Home Assistant Docker container : the `/PATH_TO_YOUR_CONFIG` in -v /PATH_TO_YOUR_CONFIG:/config (See https://www.home-assistant.io/installation/raspberrypi#platform-installation)
 - Home Assistant Core : `/home/homeassistant/.homeassistant`
 
The easiest is to use ssh and git to check the component out in the correct location. 

Replace `/PATH_TO_YOUR_CONFIG` with your config directory location:
```
export CONFIG=/PATH_TO_YOUR_CONFIG
```

Check out the component:
```
cd $CONFIG/custom_components/
git clone --recurse-submodules https://github.com/wlemkens/hass-ecometers.git
```

#### Test
You can test the component.
(Replace /dev/YOUR_USB_PORT with the correct port. For how to figure that out see below.)
```
cd $CONFIG/custom_components/hass-ecometers/ecometers/example/
ptyhon example.py /dev/YOUR_USB_PORT
```

It might take some time (order of half an hour) before some reading comes through since the data is only send periodically.


### Configuration

In your `/PATH_TO_YOUR_CONFIG/configuration.yaml`, add your config. 

If you already have a section `sensor:` you don't need to add the line with `sensor:`.
```
sensor:
```

Then the config of the sensor itself:
```
  - platform: eco_meter_s
    serial_port: /dev/YOUR_USB
    height: MAX HEIGHT OF THE WATER LEVEL
    offset: DISTANCE BETWEEN THE SENSOR AND THE MAX WATER LEVEL
```

So if you didn't have the `sensor:` part, it now looks like:
```
sensor:
  - platform: eco_meter_s
    serial_port: /dev/YOUR_USB
    height: MAX HEIGHT OF THE WATER LEVEL
    offset: DISTANCE BETWEEN THE SENSOR AND THE MAX WATER LEVEL
```

### Installation completion
Restart Home Assistant.
Settings > System > Restart (on top right)

After restart, you should have the following entities:
- sensor.tank_fill : Fill level in %
- sensor.tank_level : Fill level in cm
- sensor.tank_temperature : Temperature inside the tank
- sensor.tank_volume : Fill level in liters.

The component doesn't show up in the Integrations tab. You can find the sensors in the "Entities" tab.

### Note
It is recommended to use `/dev/serial/by-id/DEVICE_ID` to configure your usb port since this will be guarenteed to remain the same after reboot.

However, the Docker installation doesn't seem to expose these inside the container so you will need to use `/dev/ttyUSBX` where X is the corresponding number for your device.
This might change after reboot though. So you might need to check this if you get problems with the component.

## Discovering your USB port
Depending on your setup you either need something your port to be something like /dev/ttyUSB0 or /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0.

```
ls -l /dev/serial/by-id
```
This will print out something like:

```
lrwxrwxrwx 1 root root 13  9 sep 09:17 usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 -> ../../ttyUSB0
```
Other lines might be present too but this is the one we are interested in.

If you don't have any line like this, you might want to unplug your usb cable, execute the command. Replug the cable and re-execute the command.
There should be one more device after te inplugging than before. This is the device we need.
```
ls -l /dev/serial/by-id
```

If you have a Docker installation, use `/dev/ttyUSB0` (for the example above) or whatever port the arrow points to in the `ls` command.

Otherwise, use `/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0` or the equivalent that is before the arrow.

## Supported parameters
Currently only vertical cylindrical tanks (form A) are supported with no dead zone at the bottom.
*Let me know if you want extra parameters (dead zone, other tank types).*

The parameters should correspond with the configuration you used in your Eco Meter S display.

### Height
The maximum height the water level will reach.

### Offset
The distance between the sensor an the maximum water level.
