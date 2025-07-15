import serial
import csv
import time
import os

# CONFIGURE:
UART_PORT = '/dev/ttyACM0'  # or your actual port
BAUDRATE = 115200

# Open serial port
ser = serial.Serial(UART_PORT, BAUDRATE, timeout=1)
print(f"Listening on {UART_PORT} at {BAUDRATE} baud")

# State
header = None
file_handles = {}
csv_writers = {}

try:
    while True:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if not line:
            continue  # skip empty

        # Debug raw line
        print(f"RAW: {line}")

        # Header line starts with "SERVER,"
        if line.startswith("SERVER,"):
            fields = [h.strip() for h in line.split(",")]
            # Remove the first "SERVER" token
            header = fields[1:]
            print("Parsed header:", header)

        # Data line starts with a server address like "0x"
        elif line.startswith("0x"):
            if not header:
                print("WARNING: Data before header. Skipping.")
                continue

            parts = [p.strip() for p in line.split(",")]
            server = parts[0]
            values = parts[1:]
            # Pad missing fields
            while len(values) < len(header):
                values.append('')

            # Prepare CSV for this server
            fname = f"sensor_data_{server}.csv"
            if server not in csv_writers:
                f = open(fname, 'a', newline='')
                writer = csv.writer(f)
                # Write header if file is empty
                f.seek(0, os.SEEK_END)
                if f.tell() == 0:
                    writer.writerow(header)
                    f.flush()
                file_handles[server] = f
                csv_writers[server] = writer

            # Write the row
            writer = csv_writers[server]
            writer.writerow(values)
            file_handles[server].flush()
            print(f"Wrote to {fname}: {values}")

except KeyboardInterrupt:
    print("\nExiting.")
finally:
    # Close all files
    for f in file_handles.values():
        f.close()

