from abc import ABC, abstractmethod
from base64 import b64encode
import struct
import logging
import json

from homeassistant.const import ATTR_ENTITY_ID

_LOGGER = logging.getLogger(__name__)

BROADLINK_CONTROLLER = 'Broadlink'
XIAOMI_CONTROLLER = 'Xiaomi'
MQTT_CONTROLLER = 'MQTT'
ESPHOME_CONTROLLER = 'ESPHome'


def get_controller(hass, controller, controller_data, delay):
    """Return a controller compatible with the specification provided."""
    controllers = {
        BROADLINK_CONTROLLER: BroadlinkController,
        XIAOMI_CONTROLLER: XiaomiController,
        MQTT_CONTROLLER: MQTTController,
        ESPHOME_CONTROLLER: ESPHomeController
    }
    try:
        return controllers[controller](hass, controller, controller_data, delay)
    except KeyError:
        raise Exception("The controller is not supported.")


class AbstractController(ABC):
    """Representation of a controller."""
    def __init__(self, hass, controller, controller_data, delay):
        self.hass = hass
        self._controller = controller
        self._controller_data = controller_data
        self._delay = delay

    @abstractmethod
    async def send(self, command):
        """Send a command."""
        pass

    @abstractmethod
    async def exist(self):
        return True


class BroadlinkController(AbstractController):
    """Controls a Broadlink device."""

    def raw2broadlink(self, pulses):
        array = bytearray()

        for pulse in pulses:
            pulse = int(pulse * 269 / 8192)

            if pulse < 256:
                array += bytearray(struct.pack('>B', pulse))
            else:
                array += bytearray([0x00])
                array += bytearray(struct.pack('>H', pulse))

        packet = bytearray([0x26, 0x00])
        packet += bytearray(struct.pack('<H', len(array)))
        packet += array
        packet += bytearray([0x0d, 0x05])

        # Add 0s to make ultimate packet size a multiple of 16 for 128-bit AES encryption.
        remainder = (len(packet) + 4) % 16
        if remainder:
            packet += bytearray(16 - remainder)
        return packet

    async def send(self, command):
        """Send a command."""
        command = self.raw2broadlink(command)
        command = b64encode(command).decode('utf-8')
        commands = ['b64:' + command]

        service_data = {
            ATTR_ENTITY_ID: self._controller_data,
            'command':  commands,
            'delay_secs': self._delay
        }
        
        await self.hass.services.async_call(
            'remote', 'send_command', service_data)

    async def exist(self):
        return self.hass.states.get(self._controller_data) is not None


class XiaomiController(AbstractController):
    """Controls a Xiaomi device."""

    async def send(self, command):
        """Send a command."""
        service_data = {
            ATTR_ENTITY_ID: self._controller_data,
            'command':  self._encoding.lower() + ':' + command
        }

        await self.hass.services.async_call(
            'remote', 'send_command', service_data)


class MQTTController(AbstractController):
    """Controls a MQTT device."""

    async def send(self, command):
        """Send a command."""
        service_data = {
            'topic': self._controller_data,
            'payload': json.dumps(command)
        }

        await self.hass.services.async_call(
            'mqtt', 'publish', service_data)
    
    async def exist(self):
        return self.hass.services.has_service('mqtt', 'publish')


class ESPHomeController(AbstractController):
    """Controls a ESPHome device."""
    def __init__(self, hass, controller, controller_data, delay):
        super().__init__(hass, controller, controller_data, delay)
        self._controller_data = controller_data if '.' not in controller_data else controller_data.split('.')[1]
    
    async def send(self, command):
        raw = []
        for i in range(0, len(command)):
            if i % 2 == 0:
                raw.append(command[i])
            else:
                raw.append(-command[i])

        service_data = {'command':  raw}

        await self.hass.services.async_call(
            'esphome', self._controller_data, service_data)
    
    async def exist(self):
        return self.hass.services.has_service('esphome', self._controller_data)
