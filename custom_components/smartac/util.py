from collections import defaultdict
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
)
from .irext import MODE_AUTO, MODE_COOL, MODE_DRY, MODE_FAN, MODE_HEAT
from .irext import SPEED_AUTO, SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM
from .irext import POWER_OFF, POWER_ON
from .irext import AC

mode_map = {MODE_AUTO: HVAC_MODE_AUTO, MODE_COOL: HVAC_MODE_COOL,
            MODE_DRY: HVAC_MODE_DRY, MODE_FAN: HVAC_MODE_FAN_ONLY, MODE_HEAT: HVAC_MODE_HEAT}
speed_map = {SPEED_AUTO: FAN_AUTO, SPEED_HIGH: FAN_HIGH,
             SPEED_LOW: FAN_LOW, SPEED_MEDIUM: FAN_MEDIUM}


def bin_to_json(bin_data):
    """Validate that this is a valid topic name/filter."""
    decode_json = {}
    decode_json['manufacturer'] = 'hass'
    decode_json['precision'] = 1

    ac = AC(bin_data)
    modes = ac.get_supported_mode()
    decode_json['operationModes'] = [mode_map[m] for m in modes]

    speeds = set()
    temperature = set()

    decode_json["commands"] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict)))
    for m in modes:
        for s in (ac.get_supported_wind_speed(m) or [SPEED_AUTO]):
            speeds.add(s)
            for t in (ac.get_temperature_range(m) or [26]):
                temperature.add(t)
                mode_key = mode_map[m]
                speed_key = speed_map[s]
                temperature_key = "%d" % t
                raw = ac.ir_decode(POWER_ON, t, m, s)
                decode_json["commands"][mode_key][speed_key][temperature_key] = raw
    raw = ac.ir_decode(POWER_OFF, 26, MODE_AUTO, SPEED_AUTO)

    decode_json["commands"]["off"] = raw

    decode_json['fanModes'] = [speed_map[s] for s in speeds]
    decode_json['minTemperature'] = min(temperature)
    decode_json['maxTemperature'] = max(temperature)
   
    return decode_json
