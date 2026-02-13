"""
SensorSwarm binary message codec.

Lightweight binary format for Leaf <-> Hub communication.
MicroPython-compatible (uses only `struct` module).

Frame layout (5–245 bytes, fits ESP-NOW 250 B limit):
┌───────┬─────────┬──────────┬──────────┬─────────┬──────────┐
│ Magic │ Version │ Msg Type │ Leaf ID  │ Payload │ Checksum │
│  1 B  │   1 B   │   1 B    │   1 B    │ 0-240 B │   1 B   │
│ 0x53  │  0x01   │          │  0–255   │         │  XOR     │
└───────┴─────────┴──────────┴──────────┴─────────┴──────────┘
"""

import struct

MAGIC = 0x53
VERSION = 0x01
HEADER_SIZE = 4   # magic + version + msg_type + leaf_id
CHECKSUM_SIZE = 1
MAX_PAYLOAD = 240

# ── Message types ────────────────────────────────────────────

MSG_SENSOR_REPORT = 0x01
MSG_HEARTBEAT     = 0x02
MSG_WAKE_NOTIFY   = 0x03
MSG_REGISTER      = 0x04
MSG_COMMAND       = 0x80
MSG_CONFIG        = 0x81
MSG_TIME_SYNC     = 0x82
MSG_ACK           = 0xFE
MSG_WAKE          = 0xFF

# ── Channel types (sensor data) ─────────────────────────────

CH_TEMPERATURE    = 0x01
CH_HUMIDITY       = 0x02
CH_PRESSURE       = 0x03
CH_CO2            = 0x04
CH_ILLUMINANCE    = 0x05
CH_PIR_MOTION     = 0x06
CH_GAS_RESISTANCE = 0x07
CH_SOIL_MOISTURE  = 0x08
CH_PH             = 0x09
CH_EC             = 0x0A
CH_BATTERY_MV     = 0x0B
CH_DOOR           = 0x0C
CH_WATER_LEVEL    = 0x0D
CH_SOUND_LEVEL    = 0x0E

CHANNEL_NAMES = {
    CH_TEMPERATURE:    "temperature",
    CH_HUMIDITY:       "humidity",
    CH_PRESSURE:       "pressure",
    CH_CO2:            "co2",
    CH_ILLUMINANCE:    "illuminance",
    CH_PIR_MOTION:     "motion",
    CH_GAS_RESISTANCE: "gas_resistance",
    CH_SOIL_MOISTURE:  "soil_moisture",
    CH_PH:             "ph",
    CH_EC:             "ec",
    CH_BATTERY_MV:     "battery_mv",
    CH_DOOR:           "door",
    CH_WATER_LEVEL:    "water_level",
    CH_SOUND_LEVEL:    "sound_level",
}

# Reverse lookup: name -> channel type
CHANNEL_BY_NAME = {v: k for k, v in CHANNEL_NAMES.items()}

# ── Capability types (superset of channel types) ────────────

CAP_RELAY    = 0x80
CAP_PWM      = 0x81
CAP_NEOPIXEL = 0x82

CAPABILITY_NAMES = dict(CHANNEL_NAMES)
CAPABILITY_NAMES.update({
    CAP_RELAY:    "relay",
    CAP_PWM:      "pwm",
    CAP_NEOPIXEL: "neopixel",
})

# ── Hardware types ───────────────────────────────────────────

HW_ESP32  = 0x01
HW_NRF54  = 0x02
HW_ATTINY = 0x03
HW_PICO   = 0x04

HW_NAMES = {
    HW_ESP32:  "esp32",
    HW_NRF54:  "nrf54",
    HW_ATTINY: "attiny",
    HW_PICO:   "pico",
}

# ── Command IDs ──────────────────────────────────────────────

CMD_SET_STATE    = 0x01
CMD_SET_PWM      = 0x02
CMD_READ_NOW     = 0x03
CMD_SET_INTERVAL = 0x04
CMD_DEEP_SLEEP   = 0x05
CMD_RESET        = 0x06

# ── Checksum ─────────────────────────────────────────────────

def _xor_checksum(data):
    """XOR all bytes."""
    cs = 0
    for b in data:
        cs ^= b
    return cs & 0xFF


# ── Encode / Decode ──────────────────────────────────────────

def encode(msg_type, leaf_id, payload=b""):
    """Build a complete frame (bytes)."""
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload too large")
    header = struct.pack("BBBB", MAGIC, VERSION, msg_type, leaf_id)
    body = header + payload
    cs = _xor_checksum(body)
    return body + struct.pack("B", cs)


def decode(raw):
    """Parse a frame. Returns (msg_type, leaf_id, payload) or raises ValueError."""
    if len(raw) < HEADER_SIZE + CHECKSUM_SIZE:
        raise ValueError("frame too short")
    magic, ver, msg_type, leaf_id = struct.unpack("BBBB", raw[:4])
    if magic != MAGIC:
        raise ValueError("bad magic")
    if ver != VERSION:
        raise ValueError("unsupported version")
    payload = raw[4:-1]
    cs = raw[-1]
    if _xor_checksum(raw[:-1]) != cs:
        raise ValueError("checksum mismatch")
    return msg_type, leaf_id, payload


# ── Payload helpers ──────────────────────────────────────────

def encode_sensor_report(channels):
    """
    channels: dict  { channel_type_int: float_value, ... }
              or    { "temperature": 22.5, ... }  (name lookup)
    Returns payload bytes.
    """
    items = []
    for k, v in channels.items():
        if isinstance(k, str):
            k = CHANNEL_BY_NAME[k]
        items.append((k, float(v)))
    buf = struct.pack("B", len(items))
    for ch, val in items:
        buf += struct.pack("B", ch) + struct.pack("<f", val)
    return buf


def decode_sensor_report(payload):
    """Returns dict { channel_name: float_value }."""
    n = payload[0]
    result = {}
    offset = 1
    for _ in range(n):
        ch = payload[offset]
        val = struct.unpack_from("<f", payload, offset + 1)[0]
        name = CHANNEL_NAMES.get(ch, f"unknown_0x{ch:02x}")
        result[name] = round(val, 4)
        offset += 5
    return result


def encode_heartbeat(battery_mv=0, uptime_sec=0):
    """HEARTBEAT payload: battery(u16) + uptime(u32)."""
    return struct.pack("<HI", int(battery_mv), int(uptime_sec))


def decode_heartbeat(payload):
    """Returns dict { battery_mv, uptime_sec }."""
    batt, uptime = struct.unpack("<HI", payload[:6])
    return {"battery_mv": batt, "uptime_sec": uptime}


def encode_register(hw_type, capabilities):
    """
    capabilities: list of int capability codes
    Returns payload bytes.
    """
    buf = struct.pack("BB", hw_type, len(capabilities))
    for cap in capabilities:
        buf += struct.pack("B", cap)
    return buf


def decode_register(payload):
    """Returns dict { hw_type: str, capabilities: [str, ...] }."""
    hw = payload[0]
    n = payload[1]
    caps = []
    for i in range(n):
        c = payload[2 + i]
        caps.append(CAPABILITY_NAMES.get(c, f"unknown_0x{c:02x}"))
    return {
        "hw_type": HW_NAMES.get(hw, f"unknown_0x{hw:02x}"),
        "capabilities": caps,
    }


def encode_command(cmd_id, args=b""):
    """COMMAND payload: cmd_id(1B) + arg_len(1B) + args."""
    if isinstance(args, (list, tuple)):
        args = bytes(args)
    return struct.pack("BB", cmd_id, len(args)) + args


def decode_command(payload):
    """Returns dict { cmd_id, args: bytes }."""
    cmd_id = payload[0]
    arg_len = payload[1]
    args = payload[2:2 + arg_len]
    return {"cmd_id": cmd_id, "args": args}


def encode_wake_notify(woken_leaf_id):
    """WAKE_NOTIFY payload: the leaf_id of the device that was woken."""
    return struct.pack("B", woken_leaf_id)


def decode_wake_notify(payload):
    """Returns int woken_leaf_id."""
    return payload[0]


def encode_time_sync(epoch_seconds):
    """TIME_SYNC payload: 4-byte epoch."""
    return struct.pack("<I", int(epoch_seconds))


def decode_time_sync(payload):
    """Returns int epoch_seconds."""
    return struct.unpack("<I", payload[:4])[0]
