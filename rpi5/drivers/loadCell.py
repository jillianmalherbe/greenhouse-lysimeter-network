"""
######################################################################
README:

This version runs in python 3.x. It will first prompt the user to
empty the scale. Then prompt user to place an item with a known weight
on the scale and input weight as INT.

The offset and scale will be adjusted accordingly and displayed for
convenience.

The user can choose to [0] exit, [1] recalibrate, or [2] display the
current offset and scale values and weigh a new item to test the accuracy
of the offset and scale values!
#######################################################################
"""

import RPi.GPIO as GPIO
import time
import sys
from hx711 import HX711

class loadCell:
    #Can print the mass and calibrate the load cell

    # constructor for the load cell class
    def __init__(self):
        # Make sure you correct these to the correct pins for DOUT and SCK.
        # gain is set to 128 as default, change as needed.
        self.hx = HX711(15, 14, 128)
        self.setup()

    def setup(self):
        # code run once to set up the sensor
        print("Initializing.\n Please ensure that the scale is empty.")
        scale_ready = False
        while not scale_ready:
            if (GPIO.input(self.hx.DOUT) == 0):
                scale_ready = False
            if (GPIO.input(self.hx.DOUT) == 1):
                print("Initialization complete!")
                scale_ready = True
                #global logger
                #logger = l.Logger()

    def calibrate(self):
        # calibrates the sensor with a known mass
        readyCheck = input("Remove any items from scale. Press any key when ready.")
        offset = self.hx.read_average()
        print("Value at zero (offset): {}".format(offset))
        self.hx.set_offset(offset)
        print("Please place an item of known weight on the scale.")

        readyCheck = input("Press any key to continue when ready.")
        measured_weight = (self.hx.read_average()-self.hx.get_offset())
        item_weight = input("Please enter the item's weight in grams.\n>")
        scale = int(measured_weight)/int(item_weight)
        self.hx.set_scale(scale)
        print("Scale adjusted for grams: {}".format(scale))

    # gets the offset of an item
    def get_offset(self):
        offset = self.hx.get_offset()
        self.hx.power_down()
        time.sleep(.001)
        self.hx.power_up()
        return offset

    # gets the scale of an item
    def get_scale(self):
        scale = self.hx.get_scale()
        self.hx.power_down()
        time.sleep(.001)
        self.hx.power_up()
        return scale

    # gets the mass of an item
    def get_mass(self):
        mass = self.hx.get_grams()
        self.hx.power_down()
        time.sleep(.001)
        self.hx.power_up()
        return mass

