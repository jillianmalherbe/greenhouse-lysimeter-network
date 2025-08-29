import time

import board

import adafruit_lps28
import adafruit_scd4x
import datetime

i2c = board.I2C()

lps28_sensor = adafruit_lps28.LPS28(i2c)
scd41_sensor = adafruit_scd4x.SCD4X(i2c)
print("Serial number:", [hex(i) for i in scd41_sensor.serial_number])

scd41_sensor.start_periodic_measurement()

print("Sensor Readings:")
print("-" * 40)

while True:
    print(f"Timestamp: {datetime.datetime.now()}")

    if lps28_sensor.data_ready:
        print(f"LPS28 Pressure: {lps28_sensor.pressure:.1f} hPa")
        print(f"LPS28 Temperature: {lps28_sensor.temperature:.1f} degrees Celcius")
    if scd41_sensor.data_ready:
        print("SCD41 CO2: %d ppm" % scd41_sensor.CO2)
        print("SDC41 Temperature: %0.1f *C" % scd41_sensor.temperature)
        print("SCD41 Humidity: %0.1f %%" % scd41_sensor.relative_humidity)
        print()
    time.sleep(5)
