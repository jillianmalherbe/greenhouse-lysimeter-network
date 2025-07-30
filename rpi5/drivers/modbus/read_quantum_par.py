import minimalmodbus
import serial  # for parity constants
import time
import struct # For unpacking raw bytes into specific data types

# --- Configuration ---
SERIAL_PORT = '/dev/ttyAMA0'
SLAVE_ADDRESS = 5
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
CALIBRATED_OUTPUT = 0
DETECTOR_MILLIVOLTS = 2
IMMERSED_OUTPUT = 4
SOLAR_OUTPUT = 6


# Read/Write registers (function codes 0x3 and 0x10)
DEVICE_ADDRESS_REGISTER = 16
MODEL_REGISTER = 18
SERIAL_NUMBER_REGISTER = 20
MULTIPLIER = 28
OFFSET = 30
IMMERSION_FACTOR = 32
SOLAR_MULTIPLIER = 34
RUNNING_AVERAGE = 36
HEATER_STATUS = 38


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
    print(f"\n--- Reading data from SQ-522 at {SERIAL_PORT}, Address {SLAVE_ADDRESS} ---")
    try:
        # --- Read Measurement Registers (32-bit floats) ---


        calibrated_output = client.read_float(CALIBRATED_OUTPUT, functioncode=3, byteorder=0x00)
        detector_millivolts = client.read_float(DETECTOR_MILLIVOLTS, functioncode=3, byteorder=0x00)
        immersed_output = client.read_float(IMMERSED_OUTPUT, functioncode=3, byteorder=0x00)
        solar_output = client.read_float(SOLAR_OUTPUT, functioncode=3, byteorder=0x00)

        print(f"Calibrated Output: {calibrated_output:.2f} u-mol m^-2 s^-1")
        print(f"Detector: {detector_millivolts:.2f} mV")
        print(f"Immersed Output: {immersed_output:.2f} u-mol m^-2 s^-1")
        print(f"Solar Output: {solar_output:.2f} u-mol m^-2 s^-1")


        device_address = client.read_float(DEVICE_ADDRESS_REGISTER, functioncode=3, byteorder=0x00)
        model = client.read_float(MODEL_REGISTER, functioncode=3, byteorder=0x00)
        serial_number = client.read_float(SERIAL_NUMBER_REGISTER, functioncode=3, byteorder=0x00)
        multiplier = client.read_float(MULTIPLIER, functioncode=3, byteorder=0x00)
        offset = client.read_float(OFFSET, functioncode=3, byteorder=0x00)
        immersion_factor = client.read_float(IMMERSION_FACTOR, functioncode=3, byteorder=0x00)
        solar_multiplier = client.read_float(SOLAR_MULTIPLIER, functioncode=3, byteorder=0x00)
        running_average = client.read_float(RUNNING_AVERAGE, functioncode=3, byteorder=0x00)
        heater_status = client.read_float(HEATER_STATUS, functioncode=3, byteorder=0x00)

        print(f"------------------------------------")
        print(f"Device Address: {device_address}")
        print(f"Model: '{model}'")
        print(f"Serial Number: {serial_number}")
        print(f"Multiplier: {multiplier}")
        print(f"Offset: {offset}")
        print(f"Immersion Factor: {immersion_factor}")
        print(f"Solar Multiplier: {solar_multiplier}")
        print(f"Running Average: {running_average}")
        print(f"Heater Status: {heater_status}")


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


def change_sensor_address(float):
    try:
        client.write_float(DEVICE_ADDRESS_REGISTER, float, byteorder=0)
        print(f"Heater set to: {status}")
    except serial.SerialException as e:
        print(f"Serial port error: {e}. Cannot toggle heater.")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus communication error while toggling heater: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while toggling heater: {e}")



def toggle_heater(state: bool):
    """
    Toggles the heater on (True) or off (False).
    """
    if bool==True:
        state = 1.0
        status = 'ON'
    else:
        state = 0.0
        status = 'OFF'

    try:
        client.write_float(HEATER_STATUS, state, byteorder=0)
        print(f"Heater set to: {status}")
    except serial.SerialException as e:
        print(f"Serial port error: {e}. Cannot toggle heater.")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus communication error while toggling heater: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while toggling heater: {e}")

# --- Execute ---
if __name__ == "__main__":

    change_sensor_address(5.0)
    read_sensor_data()

    # Example of toggling heater (uncomment to use)
    #print("\n--- Toggling Heater ON ---")
    #toggle_heater(True)
    # time.sleep(5)
    # read_sensor_data()

    print("\n--- Toggling Heater OFF ---")
    toggle_heater(False)
    # time.sleep(2)
    # read_sensor_data()
