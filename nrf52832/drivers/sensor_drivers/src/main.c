#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/drivers/adc.h>
#include "MLX90614.h"

static const struct adc_dt_spec adc_channel = ADC_DT_SPEC_GET(DT_PATH(zephyr_user));

int main(void)
{
    struct mlx90614_data data;

    int err;
	uint32_t count = 0;

	/* Define a variable of type adc_sequence and a buffer of type uint16_t */
	int16_t buf;
	struct adc_sequence sequence = {
		.buffer = &buf,
		/* buffer size in bytes, not number of samples */
		.buffer_size = sizeof(buf),
		// Optional
		//.calibrate = true,
	};

	/* Validate that the ADC peripheral (SAADC) is ready */
	if (!adc_is_ready_dt(&adc_channel)) {
		printk("ADC controller devivce %s not ready", adc_channel.dev->name);
		return 0;
	}
	/* Setup the ADC channel */
	err = adc_channel_setup_dt(&adc_channel);
	if (err < 0) {
		printk("Could not setup channel #%d (%d)", 0, err);
		return 0;
	}
	/* Initialize the ADC sequence */
	err = adc_sequence_init_dt(&adc_channel, &sequence);
	if (err < 0) {
		printk("Could not initalize sequnce");
		return 0;
	}


    // Leaf IR Init
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
            printk("\nSensor read error\n");
        }
        k_msleep(2000);
        
        int val_mv;

		/* Read a sample from the ADC */
		err = adc_read(adc_channel.dev, &sequence);
		if (err < 0) {
			printk("Could not read (%d)", err);
			continue;
		}

		val_mv = (int)buf;
		printk("ADC reading[%u]: %s, channel %d: Raw: %d", count++, adc_channel.dev->name,
			adc_channel.channel_id, val_mv);

		/* Convert raw value to mV*/
		err = adc_raw_to_millivolts_dt(&adc_channel, &val_mv);
		/* conversion to mV may not be supported, skip if not */
		if (err < 0) {
			printk(" (value in mV not available)\n");
		} else {
			printk(" = %d mV", val_mv);
		}

		k_sleep(K_MSEC(1000));

    }
    return 0;
}




