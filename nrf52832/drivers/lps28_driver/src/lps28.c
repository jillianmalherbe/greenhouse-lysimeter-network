#include "lps28.h"
#include <zephyr/logging/log.h>
#include <zephyr/sys/printk.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/kernel.h>

LOG_MODULE_REGISTER(lps28_driver, CONFIG_LOG_DEFAULT_LEVEL);

/* LPS28 register definitions */
#define LPS28_WHOAMI_REG     0x0F
#define LPS28_CHIP_ID        0xB4
#define LPS28_CTRL_REG1      0x10
#define LPS28_CTRL_REG2      0x11
#define LPS28_STATUS_REG     0x27
#define LPS28_TEMP_OUT_L     0x2B
#define LPS28_PRESS_OUT_XL   0x28

#define I2C_NODE DT_NODELABEL(mysensor)
static const struct i2c_dt_spec dev_i2c = I2C_DT_SPEC_GET(I2C_NODE);

/* Initialize the sensor: check WHOAMI, reset, set one‐shot mode */
int lps28_init(void)
{
    if (!device_is_ready(dev_i2c.bus)) {
        printk("I2C bus %s is not ready!\n", dev_i2c.bus->name);
        return -ENODEV;
    }

    /* Read WHOAMI to verify sensor is present */
    uint8_t id = 0;
    uint8_t reg = LPS28_WHOAMI_REG;
    if (i2c_write_read_dt(&dev_i2c, &reg, 1, &id, 1) != 0 || id != LPS28_CHIP_ID) {
        printk("LPS28 not found or ID mismatch! Read: 0x%02X\n", id);
        return -ENODEV;
    }
    LOG_INF("LPS28 found! WHOAMI = 0x%02X", id);

    /* Perform a software reset */
    uint8_t reset_cmd[] = { LPS28_CTRL_REG2, 0x04 };
    i2c_write_dt(&dev_i2c, reset_cmd, 2);
    k_msleep(100);

    /* Set FS_MODE = 1 (continuous update off), BDU = 1 (block data update) */
    uint8_t ctrl2[] = { LPS28_CTRL_REG2, 0x48 };
    i2c_write_dt(&dev_i2c, ctrl2, 2);

    /* Set ODR = 0 → one‐shot mode only (no continuous sampling) */
    uint8_t ctrl1[] = { LPS28_CTRL_REG1, 0x00 };
    i2c_write_dt(&dev_i2c, ctrl1, 2);

    return 0;
}

/*
 * Trigger a one‐shot conversion, poll STATUS until both temp+press ready,
 * read raw bytes, convert to floats, and store into *data.
 */
int lps28_fetch(struct lps28_data *data)
{
    if (!data) {
        return -EINVAL;
    }

    /* 1) Trigger one‐shot measurement */
    uint8_t trigger_cmd[] = { LPS28_CTRL_REG2, 0x49 };
    if (i2c_write_dt(&dev_i2c, trigger_cmd, 2) != 0) {
        printk("Failed to trigger one‐shot\n");
        return -EIO;
    }

    /* 2) Poll STATUS_REG until both temperature & pressure are ready (bits 0 & 1 = 1) */
    uint8_t status = 0;
    uint8_t status_reg = LPS28_STATUS_REG;
    for (int i = 0; i < 50; i++) {
        if (i2c_write_read_dt(&dev_i2c, &status_reg, 1, &status, 1) != 0) {
            printk("Failed to read status\n");
            return -EIO;
        }
        if ((status & 0x03) == 0x03) {
            break; /* both T & P ready */
        }
        k_msleep(10);
    }
    if ((status & 0x03) != 0x03) {
        printk("LPS28 data not ready in time (status=0x%02X)\n", status);
        return -EIO;
    }

    /* 3) Read raw temperature (2 bytes: OUT_L, OUT_H) */
    uint8_t temp_raw[2] = {0};
    if (i2c_burst_read_dt(&dev_i2c, LPS28_TEMP_OUT_L, temp_raw, 2) != 0) {
        printk("I2C read temp failed\n");
        return -EIO;
    }
    int16_t raw_temp = (int16_t)((temp_raw[1] << 8) | temp_raw[0]);
    /* Convert LPS28 raw to °C: datasheet says: T = raw_temp * 0.01 */
    data->temp_c = raw_temp * 0.01f;

    /* 4) Read raw pressure (3 bytes: OUT_XL, OUT_L, OUT_H) */
    uint8_t press_raw[3] = {0};
    if (i2c_burst_read_dt(&dev_i2c, LPS28_PRESS_OUT_XL, press_raw, 3) != 0) {
        printk("I2C read pressure failed\n");
        return -EIO;
    }
    int32_t raw_press = ((int32_t)press_raw[2] << 16) |
                        ((int32_t)press_raw[1] << 8) |
                        (int32_t)press_raw[0];
    /* Convert LPS28 raw to hPa: datasheet says: P(hPa) = raw_press / 2048.0 */
    data->press_hpa = raw_press / 2048.0f;

    return 0;
}

