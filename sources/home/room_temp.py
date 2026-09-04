"""Room temperature - STUB. Fill in once the sensor/integration is chosen (see
docs/HARDWARE.md: options include a GPIO/I2C sensor like a DHT22, or reading a smart
plug/Home Assistant API). Wire the real reading into collect() below; keep the entry shape."""

from core.status import write_entries


def collect():
    entries = [{"id": "room_temp", "category": "home", "label": "Room temperature",
                "value": "not configured", "status": "stale"}]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
