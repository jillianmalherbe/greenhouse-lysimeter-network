/*
 * Bluetooth GATT service sending LPS28 temperature and pressure
 * from nRF52832 with Zephyr + peripheral_lbs adaptation
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/printk.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <stdio.h>

#define SLEEP_TIME_MS 2000
#define LPS28_WHOAMI_REG     0x0F
#define LPS28_CHIP_ID        0xB4
#define LPS28_CTRL_REG1      0x10
#define LPS28_CTRL_REG2      0x11
#define LPS28_STATUS_REG     0x27
#define LPS28_TEMP_OUT_L     0x2B
#define LPS28_PRESS_OUT_XL   0x28

#define I2C_NODE DT_NODELABEL(mysensor)
static const struct i2c_dt_spec dev_i2c = I2C_DT_SPEC_GET(I2C_NODE);

static float temperature_c = 0.0f;
static float pressure_hpa = 0.0f;

static ssize_t read_temp(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                         void *buf, uint16_t len, uint16_t offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset, &temperature_c, sizeof(temperature_c));
}

static ssize_t read_press(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                          void *buf, uint16_t len, uint16_t offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset, &pressure_hpa, sizeof(pressure_hpa));
}

BT_GATT_SERVICE_DEFINE(sensor_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_DECLARE_128(BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef0))),
    BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_128(BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef1)),
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ, read_press, NULL, &pressure_hpa),
    BT_GATT_CCC(NULL, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
    BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_128(BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef2)),
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ, read_temp, NULL, &temperature_c),
    BT_GATT_CCC(NULL, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE)
);

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME, sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static const struct bt_le_adv_param adv_params = {
    .options = BT_LE_ADV_OPT_CONNECTABLE,
    .interval_min = BT_GAP_ADV_FAST_INT_MIN_2,
    .interval_max = BT_GAP_ADV_FAST_INT_MAX_2,
    .id = BT_ID_DEFAULT,
    .peer = NULL,
};

static void bt_ready(int err)
{
    if (err) {
        printk("Bluetooth init failed (err %d)\n", err);
        return;
    }

    printk("Bluetooth initialized\n");
    err = bt_le_adv_start(&adv_params, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err) {
        printk("Advertising failed to start (err %d)\n", err);
    } else {
        printk("Advertising started\n");
    }
}

int main(void)
{
    if (!device_is_ready(dev_i2c.bus)) {
        printk("I2C bus %s is not ready!\n", dev_i2c.bus->name);
        return 0;
    }

    uint8_t id = 0;
    uint8_t reg = LPS28_WHOAMI_REG;
    if (i2c_write_read_dt(&dev_i2c, &reg, 1, &id, 1) != 0 || id != LPS28_CHIP_ID) {
        printk("LPS28 not found or wrong ID! Read: 0x%02X\n", id);
        return 0;
    }
    printk("LPS28 found! WHOAMI = 0x%02X\n", id);

    uint8_t reset[] = { LPS28_CTRL_REG2, 0x04 };
    i2c_write_dt(&dev_i2c, reset, 2);
    k_msleep(100);

    uint8_t ctrl2[] = { LPS28_CTRL_REG2, 0x48 };
    i2c_write_dt(&dev_i2c, ctrl2, 2);

    uint8_t ctrl1[] = { LPS28_CTRL_REG1, 0x00 };
    i2c_write_dt(&dev_i2c, ctrl1, 2);

    bt_enable(bt_ready);

    while (1) {
        uint8_t trigger[] = { LPS28_CTRL_REG2, 0x49 };
        i2c_write_dt(&dev_i2c, trigger, 2);

        uint8_t status = 0;
        uint8_t status_reg = LPS28_STATUS_REG;
        for (int i = 0; i < 50; i++) {
            i2c_write_read_dt(&dev_i2c, &status_reg, 1, &status, 1);
            if ((status & 0x03) == 0x03) break;
            k_msleep(10);
        }

        if ((status & 0x03) != 0x03) {
            printk("Data not ready in time.\n");
            k_msleep(SLEEP_TIME_MS);
            continue;
        }

        uint8_t temp_raw[2] = {0};
        i2c_burst_read_dt(&dev_i2c, LPS28_TEMP_OUT_L, temp_raw, 2);
        int16_t raw_temp = (int16_t)((temp_raw[1] << 8) | temp_raw[0]);
        temperature_c = raw_temp * 0.01f;

        uint8_t press_raw[3] = {0};
        i2c_burst_read_dt(&dev_i2c, LPS28_PRESS_OUT_XL, press_raw, 3);
        int32_t raw_press = ((int32_t)press_raw[2] << 16) |
                            ((int32_t)press_raw[1] << 8) |
                            press_raw[0];
        pressure_hpa = raw_press / 2048.0f;

        bt_gatt_notify(NULL, &sensor_svc.attrs[2], &pressure_hpa, sizeof(pressure_hpa));
        bt_gatt_notify(NULL, &sensor_svc.attrs[5], &temperature_c, sizeof(temperature_c));

        printk("P=%.2f, T=%.2f\n", (double)pressure_hpa, (double)temperature_c);
        k_msleep(SLEEP_TIME_MS);
    }

    return 0;
}
