#include "MLX90614.h"
#include <zephyr/logging/log.h>
//#include <zephyr/sys/printk.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/kernel.h>

LOG_MODULE_REGISTER(mlx90614, CONFIG_LOG_DEFAULT_LEVEL);

/* MLX90614 I2C address is defined in dev_i2c */
/* MLX90614 RAM registers */
#define MLX90614_TA       0x06
#define MLX90614_TOBJ1    0x07

#define I2C_NODE DT_NODELABEL(mysensor)
static const struct i2c_dt_spec dev_i2c = I2C_DT_SPEC_GET(I2C_NODE);

/* --------------------------------------------------------------------------
 * Public API
 * -------------------------------------------------------------------------- */

int mlx90614_init(void)
{
    if (!device_is_ready(dev_i2c.bus)) {
        LOG_ERR("I2C bus %s not ready", dev_i2c.bus->name);
        return -ENODEV;
    }
    LOG_INF("MLX90614 init on bus %s", dev_i2c.bus->name);
    return 0;
}

int mlx90614_fetch(struct mlx90614_data *data)
{
    if (!data) {
        return -EINVAL;
    }

    uint8_t buf[3];
    uint16_t raw;
    int ret;

    /* --- Read ambient temperature (TA) --- */
    ret = i2c_burst_read_dt(&dev_i2c, MLX90614_TA, buf, sizeof(buf));
    if (ret) {
        LOG_ERR("Ambient read failed (%d)", ret);
        return -EIO;
    }
    raw = (uint16_t)buf[1] << 8 | buf[0];
    if (raw == 0) {
        LOG_ERR("Ambient raw == 0, invalid");
        return -EIO;
    }
    data->ambient = raw * 0.02 - 273.15;

    /* --- Read object temperature (TOBJ1) --- */
    ret = i2c_burst_read_dt(&dev_i2c, MLX90614_TOBJ1, buf, sizeof(buf));
    if (ret) {
        LOG_ERR("Object read failed (%d)", ret);
        return -EIO;
    }
    raw = (uint16_t)buf[1] << 8 | buf[0];
    if (raw == 0) {
        LOG_ERR("Object raw == 0, invalid");
        return -EIO;
    }
    data->object = raw * 0.02 - 273.15;

    return 0;
}


