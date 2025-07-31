#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include "MLX90614.h"


int main(void)
{
    struct mlx90614_data data;

    if (mlx90614_init() != 0) {
        printk("MLX90614 init failed\n");
        return 0;
    }
    printk("MLX90614 Sensor Successfully Initialized\n");

    while (1) {
        if (mlx90614_fetch(&data) == 0) {
            /* cast float→double to match printf’s expected varargs */
            printk("Ambient: %.2f °C, Object: %.2f °C\n",
                   (double)data.ambient,
                   (double)data.object);
        } else {
            printk("Sensor read error\n");
        }
        k_msleep(1000);
    }
}




