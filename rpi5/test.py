import minimalmodbus
import serial  # for parity constants
# (If you need DE/RE control, import RPi.GPIO as GPIO and wire as in step 1)

# 1. Configure the Instrument
client = minimalmodbus.Instrument('/dev/ttyAMA0', 1)    # Port and slave address
client.serial.baudrate   = 19200
client.serial.bytesize   = 8
client.serial.parity     = serial.PARITY_EVEN
client.serial.stopbits   = 1
client.serial.timeout    = 1     # seconds
client.mode              = minimalmodbus.MODE_RTU
client.clear_buffers_before_each_transaction = True

# 2. (Optional) DE/RE toggle on SP3485 if required:
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(17, GPIO.OUT)       # DE/RE pin on SP3485
# def send_and_receive(fn, *args, **kwargs):
#     GPIO.output(17, GPIO.HIGH)  # drive bus
#     result = fn(*args, **kwargs)
#     GPIO.output(17, GPIO.LOW)   # listen bus
#     return result

# 3. Read the PPFD registers (2 × 16‑bit words, big‑endian)
#    If it’s a 32‑bit float in big‑endian order:
ppfd = client.read_float(0, functioncode=3, byteorder=0x00)
print("PPFD:", ppfd)

#    If it’s raw counts in two registers:
counts = client.read_registers(0, 2, functioncode=3)
print("Raw counts:", counts)

