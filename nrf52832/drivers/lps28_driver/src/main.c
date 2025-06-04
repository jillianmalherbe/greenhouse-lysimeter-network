#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include "lps28.h"

#define SLEEP_TIME_MS 1000

int main(void)
{
    int err;
    struct lps28_data lps28_readings = { 0 };

    /* 1) Initialize the sensor */
    err = lps28_init();
    if (err) {
        printk("Failed to initialize LPS28 Sensor (err=%d)\n", err);
        return 0;
    }
    printk("LPS28 Sensor Successfully Initialized\n");

    /* 2) Loop: fetch + print every SLEEP_TIME_MS */
    while (1) {
        err = lps28_fetch(&lps28_readings);
        if (err) {
            printk("Unable to fetch LPS28 data (err=%d)\n", err);
        } else {
            /* Print the floats: note printk with '%.2f' expects doubles, so cast */
            printk("Temp: %.2f °C, Pressure: %.2f hPa\n",
                   (double)lps28_readings.temp_c,
                   (double)lps28_readings.press_hpa);
        }
        k_msleep(SLEEP_TIME_MS);
    }

    return 0;
}


