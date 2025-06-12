from stellarnet_driverLibs import stellarnet_driver3 as sn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

cal_path = "MyCal-C25013132-UVVIS-CR2.CAL"

# For Windows ONLY: Must be run in administrator mode
# Only need to run it one time after switch back from the SpectraWiz. Or manually run InstallDriver.exe located in stellarnet_driverLis/windows_only
# sn.installDeviceDriver()


# Function to calculate irradiance spectrum from raw data
def getWattsY(spectrometerWavelength, rawSampleDataY, rawDarkDataY, rawSampleDataCapturedIntegrationTimeInMS, calibrationFilePath, aperturePercentage=100):
    """
    Calculate the Watts/m^2 spectral data using the provided raw sample data, dark data, and calibration file.

    Args:
        spectrometerWavelength (array or list): Wavelength values for the spectrometer.
        rawSampleDataY (array or list): Raw sample spectral data directly obtained from the spectrometer, without dark subtraction.
        rawDarkDataY (array or list): Raw dark spectral data (to subtract from the sample data). The spectrometer should be covered to ensure no light enters.
        rawSampleDataCapturedIntegrationTimeInMS (float): The integration time in milliseconds at which the sample data was captured.
        calibrationFilePath (str): The path to the StellarNet .CAL calibration file. It should be a valid StellarNet calibration file.
        aperturePercentage (float, optional): Percentage of the aperture value (the amount of light entering the spectrometer). Default is 100%.

    Returns:
        numpy.ndarray: A numpy array representing the Watts/m^2 spectrum corresponding to the provided wavelengths.

    Notes:
        - `spectrometerWavelength`, `rawSampleDataY`, and `rawDarkDataY` must have the same length. The `spectrometerWavelength` array should correspond to the provided `rawSampleDataY` and `rawDarkDataY`.
    """

    # Step 1: Load the calibration data and interpolate it to match the spectrometerWavelength
    calibrationData = np.genfromtxt(calibrationFilePath, skip_header=31, skip_footer=1)  # Read the calibration data from the file
    interpolatedCalibrationDataY = np.interp(spectrometerWavelength, calibrationData[:, 0], calibrationData[:, 1], left=0, right=0)  # Interpolate calibration data

    # Step 2: Extract the calibration integration time from the .CAL file
    calibrationIntegrationTime = int(
        next(line.strip().split('=')[1]
            for line in open(calibrationFilePath, 'r') if 'Csf1' in line))  # Extract integration time from the calibration file

    # Step 3: Subtract dark data from the sample data to obtain the corrected scope data
    scopeY = np.subtract(rawSampleDataY, rawDarkDataY)  # Subtract dark data from sample data to correct for dark noise
    scopeY[scopeY < 0] = 0  # Ensure no negative values after subtraction

    # Step 4: Normalize the raw scope data based on the integration times (calibration and sample)
    normRatio = float(calibrationIntegrationTime) / float(rawSampleDataCapturedIntegrationTimeInMS)  # Calculate the normalization ratio

    # Step 5: Convert the spectral data to Watts, applying the aperture scaling
    wattsY = np.asarray(scopeY * interpolatedCalibrationDataY[:len(spectrometerWavelength)] * normRatio * (100.0 / aperturePercentage))  # Convert to Watts

    wattsY[wattsY < 0] = 0  # Ensure no negative values in the Watts data

    return {'X':spectrometerWavelength, 'Y':wattsY}  # Return the calculated Watts values



# This resturn a Version number of compilation date of driver
version = sn.version()
print(version)

# Device parameters to set
inttime = 50
scansavg = 1
smooth = 0
xtiming = 3

#init Spectrometer - Get BOTH spectrometer and wavelength
spectrometer, wav = sn.array_get_spec(0) # 0 for first channel and 1 for second channel , up to 127 spectrometers
"""
# Equivalent to get spectrometer and wav separately:
spectrometer = sn.array_get_spec_only(0)
wav = sn.getSpectrum_X(spectrometer)
"""

print(spectrometer)
sn.ext_trig(spectrometer, True)

# Get device ID
deviceID = sn.getDeviceId(spectrometer)
print('\nMy device ID: ', deviceID)

# Get current device parameter
currentParam = sn.getDeviceParam(spectrometer)

# Call to Enable or Disable External Trigger to by default is Disbale=False -> with timeout
# Enable or Disable Ext Trigger by Passing True or False, If pass True than Timeout function will be disable, so user can also use this function as timeout enable/disbale
sn.ext_trig(spectrometer,True)


# Only call this function on first call to get spectrum or when you want to change device setting.
# -- Set last parameter to 'True' throw away the first spectrum data because the data may not be true for its inttime after the update.
# -- Set to 'False' if you don't want to do another capture to throw away the first data, however your next spectrum data might not be valid.
sn.setParam(spectrometer, inttime, scansavg, smooth, xtiming, True)

# Get spectrometer data - Get BOTH X and Y in single return
#first_data = sn.array_spectrum(spectrometer, wav) # get specturm for the first time

# Get Y value ONLY :
#first_data = sn.getSpectrum_Y(spectrometer)

input("Spectrometer should not be covered, sampling light data. Press enter to take the measurement")
light_data = sn.getSpectrum_Y(spectrometer)
wav = sn.getSpectrum_X(spectrometer)
print('Light data:', light_data )

input("Spectrometer should be covered to ensure no light enters. Press enter to take the measurement")
dark_data = sn.getSpectrum_Y(spectrometer)
print('Dark data:', dark_data)

irradiance_data = getWattsY(wav, light_data, dark_data, inttime, cal_path, 100)
print('Irradiance data:', irradiance_data)

# Plot Spectrum
data = np.array(irradiance_data)
# Split into wavelength and count arrays
wavelengths = data[:, 0]
irradiance = data[:, 1]

# Create the plot
plt.figure(figsize=(10, 5))
plt.plot(wavelengths, irradiance, label='Spectrum', linewidth=1)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Irradiance')
plt.title('Spectrometer Data')
plt.grid(True)

plt.xlim(wavelengths.min(), wavelengths.max())
plt.legend()
plt.tight_layout()

# Save the plot to a file
plt.savefig("irradiance_plot.png", dpi=300)

#==============================================
# Burst FIFO mode: Not recommended with high integration time.
# burst_data_2 = sn.getBurstFifo_Y(spectrometer)
#==============================================

# Release the spectrometer before ends the program
sn.reset(spectrometer)

# For Windows ONLY: Must be run in administrator mode
# sn.uninstallDeviceDriver()
