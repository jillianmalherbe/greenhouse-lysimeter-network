import asyncio
from bleak import BleakScanner, BleakClient

TARGET_NAME = "Nordic_LBS"

async def main():
    print("🔍 Scanning for devices...")
    devices = await BleakScanner.discover()

    target_device = None
    for d in devices:
        if d.name == TARGET_NAME:
            print(f"✅ Found target device: {d.name} @ {d.address}")
            target_device = d
            break

    if not target_device:
        print("❌ Could not find device. Make sure it's advertising.")
        return

    async with BleakClient(target_device.address) as client:
        print(f"🎉 Connected to {TARGET_NAME} ({target_device.address})")
        print("Services:")
        for service in client.services:
            print(service)

asyncio.run(main())

