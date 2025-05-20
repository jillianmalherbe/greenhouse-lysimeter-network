#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/printk.h>

#define SLEEP_TIME_MS 1000

#define LPS28_WHOAMI_REG     0x0F
#define LPS28_CHIP_ID        0xB4
#define LPS28_CTRL_REG1      0x10
#define LPS28_CTRL_REG2      0x11
#define LPS28_STATUS_REG     0x27
#define LPS28_TEMP_OUT_L     0x2B
#define LPS28_PRESS_OUT_XL   0x28

#define I2C_NODE DT_NODELABEL(mysensor)

static const struct i2c_dt_spec dev_i2c = I2C_DT_SPEC_GET(I2C_NODE);

int main(void)
{
    if (!device_is_ready(dev_i2c.bus)) {
        printk("I2C bus %s is not ready!\n", dev_i2c.bus->name);
        return -1;
    }

    // WHOAMI check
    uint8_t id = 0;
    uint8_t reg = LPS28_WHOAMI_REG;
    if (i2c_write_read_dt(&dev_i2c, &reg, 1, &id, 1) != 0 || id != LPS28_CHIP_ID) {
        printk("LPS28 not found or wrong ID! Read: 0x%02X\n", id);
        return -1;
    }
    printk("LPS28 found! WHOAMI = 0x%02X\n", id);

    // Reset
    uint8_t reset[] = { LPS28_CTRL_REG2, 0x04 };
    i2c_write_dt(&dev_i2c, reset, 2);
    k_msleep(100);

    // Set FS_MODE = 1, BDU = 1
    uint8_t ctrl2[] = { LPS28_CTRL_REG2, 0x48 };
    i2c_write_dt(&dev_i2c, ctrl2, 2);

    // Set ODR = 0 (one-shot mode)
    uint8_t ctrl1[] = { LPS28_CTRL_REG1, 0x00 };
    i2c_write_dt(&dev_i2c, ctrl1, 2);

    while (1) {
        // Trigger one-shot measurement
        uint8_t trigger[] = { LPS28_CTRL_REG2, 0x49 };  // FS_MODE=1, BDU=1, ONE_SHOT=1
        i2c_write_dt(&dev_i2c, trigger, 2);

        // Wait for STATUS = 0x03
        uint8_t status = 0;
        uint8_t status_reg = LPS28_STATUS_REG;
        for (int i = 0; i < 50; i++) {
            i2c_write_read_dt(&dev_i2c, &status_reg, 1, &status, 1);
            if ((status & 0x03) == 0x03) break;
            k_msleep(10);
        }

        printk("STATUS = 0x%02X\n", status);

        if ((status & 0x03) != 0x03) {
            printk("Data not ready in time.\n");
            goto wait;
        }

        // Read temp
        uint8_t temp_raw[2] = {0};
        i2c_burst_read_dt(&dev_i2c, LPS28_TEMP_OUT_L, temp_raw, 2);
        int16_t raw_temp = (int16_t)((temp_raw[1] << 8) | temp_raw[0]);
        float temp_c = raw_temp * 0.01f;
        float temp_f = temp_c * 1.8f + 32.0f;

        // Read pressure
        uint8_t press_raw[3] = {0};
        i2c_burst_read_dt(&dev_i2c, LPS28_PRESS_OUT_XL, press_raw, 3);
        int32_t raw_press = ((int32_t)press_raw[2] << 16) |
                            ((int32_t)press_raw[1] << 8) |
                            press_raw[0];
        float pressure_hpa = raw_press / 2048.0f;

        printk("Temperature: %.2f °C / %.2f °F\n", (double)temp_c, (double)temp_f);
        printk("Pressure: %.2f hPa\n", (double)pressure_hpa);

    wait:
        k_msleep(SLEEP_TIME_MS);
    }

    return 0;
}

