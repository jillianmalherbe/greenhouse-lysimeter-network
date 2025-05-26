import CO2etal as co2
import soilMoisture as moist
import leafIR as ir
import pressure as pres
import loadCell as load
import valve as v
#import logger_csv as l
import time
from datetime import datetime

# this stores the current time
global curr_time
curr_time=time.time()

# calibrate the load cell
load_cell = load.loadCell()
load_cell.calibrate()

# strores the logger information
#logger = l.Logger()

print("\nOffset: {}\nScale: {}".format(load_cell.get_offset(), load_cell.get_scale()))
print("Item weighs {} grams.\n".format(load_cell.get_mass()))

## check if 24 hours have elapsed then turn the valve on
#def check_turn_on():
#	global curr_time
#	#if not(valve.is_on()) and curr_time-time.time()/3600 <= -24:
#	if not(valve.is_on()) and curr_time-time.time() <= -30:
#		curr_time=time.time()
#		valve.turn_on()
#
#	# turns the valve off if it has been more than 15 minutes
#	#if valve.is_on() and curr_time-time.time() <= -1800:
#	if valve.is_on() and curr_time-time.time() <= -30:
#		valve.turn_off()


# loop through and print information in the csv file
# create all sensors classes
#try:
#	co2_sensor = co2.CO2()
#except:
#	pass
#
#try:
#	moist_sensor = moist.soilMoisture()
#except:
#	pass
#try:
#	pres_sensor = pres.Pressure()
#except:
#	pass
#try:
#	ir_sensor = ir.leafIR()
#except:
#	pass
#try:
#	valve = v.Valve()
#except:
#	pass

# Run the loop function indefinitely to print the sensor information in the csv file
while True:

#	# get the c02 data
#	try:
#		print("Data available?", co2_sensor.get_data_available())
#		co2_value=co2_sensor.get_co2()
#		print("CO2:", co2_value, "PPM")
#		co2_temp=co2_sensor.get_temp()
#		print("Temperature:", co2_temp, "degrees C")
#		co2_humid=co2_sensor.get_humid()
#		print("Humidity:", co2_humid, "%%rH")
#		'''logger.collect_data("Co2 (PPM)", co2_value)
#		logger.collect_data("Co2_temp (°C)", co2_temp)
#		logger.collect_data("Co2_humid (%%rH)", co2_humid)'''
#	except:
#		pass
#
#	try:
#		# for the soil moisture sensor
#		soil_temp=str(moist_sensor.get_temp())
#		print("temp: " + soil_temp)
#		soil_moist=str(moist_sensor.get_moist())
#		print("moisture: " + soil_moist)
#		'''logger.collect_data("Soil_temp (°C)", soil_temp)
#		logger.collect_data("Soil_moist", soil_moist)'''
#	except:
#		pass
#
#	try:
#		# Read data for pressure sensor
#		bmp_temp, pressure = pres_sensor.get_temp_and_pressure()
#		bmp_temp="{text:.2f}".format(text=bmp_temp)
#		pressure="{text:.2f}".format(text=pressure)
#
#		# Print results
#		print("Temperature: ", bmp_temp, "°C, Pressure: ",pressure," Pa")
#		'''logger.collect_data("Bmp_temp (°C)", bmp_temp)
#		logger.collect_data("Pressure (Pa)", pressure)'''
#	except:
#		pass
#
#	try:
#		# Read data for leaf ir sensor
#		ambient_temp = ir_sensor.get_ambient_temp()
#		object_temp = ir_sensor.get_object_temp()
#
#		ambient_temp = "{text:.2f}".format(text=ambient_temp)
#		object_temp = "{text:.2f}".format(text=object_temp)
#
#		print("Ambient Temperature: ",ambient_temp," °C")
#		print("Object Temperature: ",object_temp," °C")
#		'''logger.collect_data("Ambient_temp (°C)", ambient_temp)
#		logger.collect_data("Object_temp (°C)", object_temp)'''
#	except:
#		pass

	mass="{}".format(load_cell.get_mass())

	print("Item weighs ",mass," grams.\n")

	# add all the variables to the logger
	'''logger.collect_data("Date", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
	logger.collect_data("Mass", mass)
	logger.log_data_csv()'''

	time.sleep(5)
	#logger.add_server()

	# check if 24 hours have elapsed then turn the valve on (also turn off if needed)
#	check_turn_on()
