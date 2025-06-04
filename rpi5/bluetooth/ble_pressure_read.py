import asyncio
from bleak import BleakScanner, BleakClient
import struct

TARGET_NAME = "nRF52_Sensor"
UUID_PRESSURE = "12345678-1234-5678-1234-56789abcdef1"
UUID_TEMPERATURE = "12345678-1234-5678-1234-56789abcdef2"

def decode_float(data):
    return struct.unpack("<f", data)[0]  # Little-endian 4-byte float

def handle_pressure(_, data):
    pressure = decode_float(data)
    print(f"🧭 Pressure: {pressure:.2f} hPa")

def handle_temperature(_, data):
    temperature = decode_float(data)
    print(f"🌡️  Temperature: {temperature:.2f} °C")

async def main():
    print("🔍 Scanning for device...")
    devices = await BleakScanner.discover()
    device = next((d for d in devices if d.name == TARGET_NAME), None)

    if not device:
        print("❌ Device not found. Is it advertising?")
        return

    async with BleakClient(device.address) as client:
        print(f"✅ Connected to {TARGET_NAME} ({device.address})")

        await client.start_notify(UUID_PRESSURE, handle_pressure)
        await client.start_notify(UUID_TEMPERATURE, handle_temperature)

        print("📡 Receiving sensor data (press Ctrl+C to stop)...")
        while True:
            await asyncio.sleep(1)

asyncio.run(main())

