import asyncio
from bleak import BleakScanner, BleakClient

TARGET_NAME = "Nordic_LBS"
UUID_LED = "00001525-1212-efde-1523-785feabcd123"
UUID_BUTTON = "00001524-1212-efde-1523-785feabcd123"

def button_callback(sender, data):
    value = int(data[0])
    print(f"🔘 Button state: {'Pressed' if value else 'Released'}")

async def main():
    print("🔍 Scanning for devices...")
    devices = await BleakScanner.discover()
    device = next((d for d in devices if d.name == TARGET_NAME), None)

    if not device:
        print("❌ Device not found.")
        return

    async with BleakClient(device.address) as client:
        print(f"🎉 Connected to {device.name} ({device.address})")

        # Read current button state
        button_value = await client.read_gatt_char(UUID_BUTTON)
        print(f"🔘 Initial button state: {'Pressed' if button_value[0] else 'Released'}")

        # Start listening for button changes
        await client.start_notify(UUID_BUTTON, button_callback)
        print("📡 Listening for button notifications...")

        # Toggle LED back and forth 5 times
        for i in range(5):
            value = i % 2
            print(f"💡 Setting LED to: {'ON' if value else 'OFF'}")
            await client.write_gatt_char(UUID_LED, bytes([value]))
            await asyncio.sleep(1)

        print("⏱️ Waiting 10s to test button press...")
        await asyncio.sleep(10)

        await client.stop_notify(UUID_BUTTON)
        print("✅ Done.")

asyncio.run(main())

