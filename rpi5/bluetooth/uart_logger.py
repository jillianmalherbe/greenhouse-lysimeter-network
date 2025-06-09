import serial
import csv
import time

# CONFIGURE:
UART_PORT = '/dev/ttyACM0'  # or your actual port
BAUDRATE = 115200
OUTPUT_CSV = 'sensor_data_plant2.csv'

# Open serial port
ser = serial.Serial(UART_PORT, BAUDRATE, timeout=1)
print(f"Listening on {UART_PORT} at {BAUDRATE} baud")

# Initialize state
csv_header = None
csv_writer = None

# Open CSV file for appending
with open(OUTPUT_CSV, 'a', newline='') as f:
    while True:
        try:
            line = ser.readline().decode('utf-8', errors='replace').strip()

            if not line:
                continue  # skip empty

            # Debug print raw line:
            print(f"RAW: {line}")

            # Check for NAMES header:
            if line.startswith("NAMES:"):
                header_str = line[len("NAMES:"):]
                csv_header = [h.strip() for h in header_str.split(",")]

                print("Parsed CSV HEADER:", csv_header)

                # Now reset CSV writer with header:
                f.seek(0, 2)  # go to end
                if f.tell() == 0:
                    # If file is empty, write header:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow(csv_header)
                    f.flush()
                    print("CSV header written")
                else:
                    # File already has data — reuse writer:
                    csv_writer = csv.writer(f)
                    print("CSV header skipped (file not empty)")

            # Check for VALUES line:
            elif line.startswith("VALUES:"):
                if not csv_writer or not csv_header:
                    print("ERROR: Got VALUES before NAMES header — skipping")
                    continue

                values_str = line[len("VALUES:"):]
                values = [v.strip() for v in values_str.split(",")]

                # Pad missing fields (in case of missing last comma etc.)
                while len(values) < len(csv_header):
                    values.append('')

                csv_writer.writerow(values)
                f.flush()
                print("CSV row written:", values)

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(1)  # pause on error

