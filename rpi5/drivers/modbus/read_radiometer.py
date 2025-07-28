import minimalmodbus
import serial  # for parity constants
import time
import struct # For unpacking raw bytes into specific data types

# --- Configuration ---
SERIAL_PORT = '/dev/ttyAMA0'
SLAVE_ADDRESS = 1
BAUDRATE = 19200
PARITY = serial.PARITY_EVEN
BYTESIZE = 8
STOPBITS = 1
TIMEOUT = 1  # seconds
MODE = minimalmodbus.MODE_RTU
CLEAR_BUFFERS = True

# --- Modbus Register Definitions (from SN-522 manual) ---
# Addresses are 0-based

# Measurements (all are 32-bit floats, 2 registers each)
# Read only registers (function code 0x3)
CALIBRATED_SHORTWAVE_UP_WATTS = 0
CALIBRATED_SHORTWAVE_DOWN_WATTS = 2
CALIBRATED_LONGWAVE_UP_WATTS = 4
CALIBRATED_LONGWAVE_DOWN_WATTS = 6
SHORTWAVE_NET_WATTS = 8
LONGWAVE_NET_WATTS = 10
TOTAL_NET_RADIATION = 12
ALBEDO = 14
SHORTWAVE_UP_MV = 16
SHORTWAVE_DOWN_MV = 18
LONGWAVE_UP_MV = 20
LONGWAVE_DOWN_MV = 22
LONGWAVE_UP_TEMPERATURE = 24
LONGWAVE_DOWN_TEMPERATURE = 26

# Read/Write registers (function codes 0x3 and 0x10)
DEVICE_ADDRESS_REGISTER = 40
MODEL_REGISTER = 42
SERIAL_NUMBER_REGISTER = 44
LONGWAVE_UP_MULTIPLIER = 52
LONGWAVE_UP_OFFSET = 54
LONGWAVE_DOWN_MULTIPLIER = 56
LONGWAVE_DOWN_OFFSET = 58
SHORTWAVE_UP_MULTIPLIER = 60
SHORTWAVE_DOWN_MULTIPLIER = 62
RUNNING_AVERAGE = 64
HEATER_STATUS = 66


# --- Initialize MinimalModbus Client ---
client = minimalmodbus.Instrument(SERIAL_PORT, SLAVE_ADDRESS)
client.serial.baudrate = BAUDRATE
client.serial.bytesize = BYTESIZE
client.serial.parity = PARITY
client.serial.stopbits = STOPBITS
client.serial.timeout = TIMEOUT
client.mode = MODE
client.clear_buffers_before_each_transaction = CLEAR_BUFFERS
# client.debug = True # Uncomment for detailed Modbus packet debugging


# --- Helper function for reading 32-bit unsigned integers ---
def read_uint32(register_address):
    """Reads a 32-bit unsigned integer (UINT32) which spans two 16-bit registers."""
    # Apogee typically uses big-endian for multi-register values
    # The 'long' type in minimalmodbus reads 32-bit signed integers.
    # For unsigned, we read the two registers and manually combine them.
    # functioncode=3 is for Read Holding Registers
    raw_registers = client.read_registers(register_address, 2, functioncode=3)
    # The manual indicates 'Most Significant Word First' for floats.
    # This implies the same for 32-bit integers.
    # So, the first register is the high word, second is the low word.
    high_word = raw_registers[0]
    low_word = raw_registers[1]
    # Combine them into a 32-bit unsigned integer
    value = (high_word << 16) | low_word
    return value


# --- Main Script Logic ---
def read_sensor_data():
    print(f"\n--- Reading data from SN-522 at {SERIAL_PORT}, Address {SLAVE_ADDRESS} ---")
    try:
        # --- Read Measurement Registers (32-bit floats) ---


        calibrated_shortwave_up_watts = client.read_float(CALIBRATED_SHORTWAVE_UP_WATTS, functioncode=3, byteorder=0x00)
        calibrated_shortwave_down_watts = client.read_float(CALIBRATED_SHORTWAVE_DOWN_WATTS, functioncode=3, byteorder=0x00)
        calibrated_longwave_up_watts = client.read_float(CALIBRATED_LONGWAVE_UP_WATTS, functioncode=3, byteorder=0x00)
        calibrated_longwave_down_watts = client.read_float(CALIBRATED_LONGWAVE_DOWN_WATTS, functioncode=3, byteorder=0x00)
        shortwave_net_watts = client.read_float(SHORTWAVE_NET_WATTS, functioncode=3, byteorder=0x00)
        longwave_net_watts = client.read_float(LONGWAVE_NET_WATTS, functioncode=3, byteorder=0x00)
        total_net_radiation = client.read_float(TOTAL_NET_RADIATION, functioncode=3, byteorder=0x00)
        albedo = client.read_float(ALBEDO, functioncode=3, byteorder=0x00)
        shortwave_up_mv = client.read_float(SHORTWAVE_UP_MV, functioncode=3, byteorder=0x00)
        shortwave_down_mv = client.read_float(SHORTWAVE_DOWN_MV, functioncode=3, byteorder=0x00)
        longwave_up_mv = client.read_float(LONGWAVE_UP_MV, functioncode=3, byteorder=0x00)
        longwave_down_mv = client.read_float(LONGWAVE_DOWN_MV, functioncode=3, byteorder=0x00)
        longwave_up_temperature = client.read_float(LONGWAVE_UP_TEMPERATURE, functioncode=3, byteorder=0x00)
        longwave_down_temperature = client.read_float(LONGWAVE_DOWN_TEMPERATURE, functioncode=3, byteorder=0x00)


        print(f"Calibrated Shortwave Up: {calibrated_shortwave_up_watts:.2f} Watts")
        print(f"Calibrated Shortwave Down: {calibrated_shortwave_down_watts:.2f} Watts")
        print(f"Calibrated Longwave Up: {calibrated_longwave_up_watts:.2f} Watts")
        print(f"Calibrated Longwave Down: {calibrated_longwave_down_watts:.2f} Watts")
        print(f"Shortwave Net: {shortwave_net_watts:.2f} Watts")
        print(f"Longwave Net: {longwave_net_watts:.2f} Watts")
        print(f"Total Net Radiation: {total_net_radiation:.2f} Watts")
        print(f"ALbedo: {albedo:.2f} Watts")
        print(f"Shortwave Up: {shortwave_up_mv:.2f} mV")
        print(f"Shortwave Down: {shortwave_down_mv:.2f} mV")
        print(f"Longwave Up: {longwave_up_mv:.2f} mV")
        print(f"Longwave Down: {longwave_down_mv:.2f} mV")
        print(f"Longwave Up Temperature: {longwave_up_temperature:.2f} degrees")
        print(f"Longwave Down Temperature: {longwave_down_temperature:.2f} degrees")


        device_address = client.read_float(CALIBRATED_SHORTWAVE_UP_WATTS, functioncode=3, byteorder=0x00)
        model = client.read_float(MODEL_REGISTER, functioncode=3, byteorder=0x00)
        serial_number = client.read_float(SERIAL_NUMBER_REGISTER, functioncode=3, byteorder=0x00)
        longwave_up_multiplier = client.read_float(LONGWAVE_UP_MULTIPLIER, functioncode=3, byteorder=0x00)
        longwave_up_offset = client.read_float(LONGWAVE_UP_OFFSET, functioncode=3, byteorder=0x00)
        longwave_down_multiplier = client.read_float(LONGWAVE_DOWN_MULTIPLIER, functioncode=3, byteorder=0x00)
        longwave_down_offset = client.read_float(LONGWAVE_DOWN_OFFSET, functioncode=3, byteorder=0x00)
        shortwave_up_multiplier = client.read_float(SHORTWAVE_UP_MULTIPLIER, functioncode=3, byteorder=0x00)
        shortwave_down_multiplier = client.read_float(SHORTWAVE_DOWN_MULTIPLIER, functioncode=3, byteorder=0x00)
        running_average = client.read_float(RUNNING_AVERAGE, functioncode=3, byteorder=0x00)
        heater_status = client.read_float(HEATER_STATUS, functioncode=3, byteorder=0x00)

        print(f"------------------------------------")
        print(f"Device Address: {device_address}")
        print(f"Model: '{model}'")
        print(f"Serial Number: {serial_number}")
        print(f"Longwave Up Multiplier: {longwave_up_multiplier}")
        print(f"Longwave Up Offset: {longwave_up_offset}")
        print(f"Longwave Down Multiplier: {longwave_down_multiplier}")
        print(f"Longwave Down Offset: {longwave_down_offset}")
        print(f"Shortwave Up Multiplier: {shortwave_up_multiplier}")
        print(f"Shortwave Down Multiplier: {shortwave_down_multiplier}")
        print(f"Running Average: {running_average}")
        print(f"heater_status: {heater_status}")




    except serial.SerialException as e:
        print(f"Serial port error: {e}. Make sure the port is correct and not in use.")
        print("Also ensure `dtoverlay=uart0-pi5` is in /boot/firmware/config.txt and `raspi-config` has UART enabled.")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus communication error: {e}. Check wiring, power, and sensor address.")
        print("This could also mean the register addresses/types are not exactly as expected.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # This block ensures the serial port is closed even if an error occurs
        if client.serial.is_open:
            client.serial.close()
            print("Serial port closed.")


def toggle_heater(state: bool):
    """
    Toggles the heater on (True) or off (False).
    Heater Coil Register 0
    """
    try:
        client.write_register(HEATER_STATUS, 1, number_of_decimals=0, functioncode=6, signed=False)
        print(f"Heater set to: {'ON' if state else 'OFF'}")
    except serial.SerialException as e:
        print(f"Serial port error: {e}. Cannot toggle heater.")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus communication error while toggling heater: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while toggling heater: {e}")

# --- Execute ---
if __name__ == "__main__":
    read_sensor_data()

    # Example of toggling heater (uncomment to use)
    #print("\n--- Toggling Heater ON ---")
    #toggle_heater(True)
    # time.sleep(5)
    # read_sensor_data()

    # print("\n--- Toggling Heater OFF ---")
    # toggle_heater(False)
    # time.sleep(2)
    # read_sensor_data()
