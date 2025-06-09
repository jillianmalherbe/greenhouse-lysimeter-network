/*
 * Copyright (c) 2020 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#include <zephyr/bluetooth/bluetooth.h>
#include <bluetooth/mesh/models.h>
#include <dk_buttons_and_leds.h>
#include "model_handler.h"
#include <bluetooth/mesh/sensor_types.h>

#define GET_DATA_INTERVAL	1000
#define GET_DATA_INTERVAL_QUICK 500
#define MOTION_TIMEOUT		K_SECONDS(60)

/* Replace these with your actual NetKey/AppKey indices and TTL */
#define NET_IDX            0
#define APP_IDX            0
#define DEFAULT_TTL        7

static const uint16_t server_addrs[] = { 0x0037, 0x003F /*, … */ };

typedef struct {
    uint8_t                           elem_offset;    /* 0 = primary, 1 = Element 1, … */
    const struct bt_mesh_sensor_type *type;
    const char                       *name;
} sensor_def_t;

static const sensor_def_t sensor_defs[] = {
    { .elem_offset = 0, .type = &bt_mesh_sensor_present_amb_light_level,        .name = "Ambient Light"       },
    { .elem_offset = 1, .type = &bt_mesh_sensor_presence_detected,              .name = "Time Since Presenc"  },
    { .elem_offset = 2, .type = &bt_mesh_sensor_time_since_motion_sensed,       .name = "Time Since Motion"   },
    { .elem_offset = 3, .type = &bt_mesh_sensor_people_count,                   .name = "People Count"        },
    { .elem_offset = 4, .type = &bt_mesh_sensor_present_dev_op_temp,            .name = "Chip Temp"           },
    { .elem_offset = 5, .type = &bt_mesh_sensor_present_amb_temp,               .name = "Sensor Temp"         },
    { .elem_offset = 6, .type = &bt_mesh_sensor_pressure,                       .name = "Pressure"            },
};

/* total sensors = servers × types */
#define SENSOR_COUNT  (ARRAY_SIZE(server_addrs) * ARRAY_SIZE(sensor_defs))

/* Your table to store values + valid flags + name strings */
typedef struct {
    const char                        *name;
    struct bt_mesh_msg_ctx            ctx;
    const struct bt_mesh_sensor_type *type;
    struct bt_mesh_sensor_value       value;
    bool                              valid;
} sensor_record_t;

static sensor_record_t sensor_table[SENSOR_COUNT];
// end

static void init_sensor_table(void)
{
    const size_t n_defs = ARRAY_SIZE(sensor_defs);
    for (size_t srv = 0; srv < ARRAY_SIZE(server_addrs); srv++) {
        uint16_t primary = server_addrs[srv];

        for (size_t s = 0; s < n_defs; s++) {
            size_t idx = srv * n_defs + s;

            sensor_table[idx].name = sensor_defs[s].name;
            sensor_table[idx].type = sensor_defs[s].type;
            sensor_table[idx].valid = false;

            /* pre‐build the context if you like, or rebuild in get_data() */
            sensor_table[idx].ctx.net_idx  = NET_IDX;
            sensor_table[idx].ctx.app_idx  = APP_IDX;
            sensor_table[idx].ctx.addr     = primary + sensor_defs[s].elem_offset;
            sensor_table[idx].ctx.send_ttl = DEFAULT_TTL;
        }
    }
}


static bool is_occupied;
static struct k_work_delayable motion_timeout_work;


static void motion_timeout(struct k_work *work)
{
	is_occupied = false;
	printk("Area is now vacant.\n");
}

static void sensor_cli_data_cb(struct bt_mesh_sensor_cli *cli,
                               struct bt_mesh_msg_ctx   *ctx,
                               const struct bt_mesh_sensor_type *sensor,
                               const struct bt_mesh_sensor_value *value)
{
    for (int i = 0; i < SENSOR_COUNT; i++) {
        /* Match on both property ID *and* element/server address */
        if (sensor_table[i].type->id == sensor->id
            && sensor_table[i].ctx.addr  == ctx->addr) {
            sensor_table[i].value = *value;
            sensor_table[i].valid = true;
            printk("Received %s from 0x%04x (id=0x%04X)\n",
                   sensor_table[i].name,
                   ctx->addr,
                   sensor->id);
            break;
        }
    }
}


static void sensor_cli_series_entry_cb(struct bt_mesh_sensor_cli *cli, struct bt_mesh_msg_ctx *ctx,
				       const struct bt_mesh_sensor_type *sensor, uint8_t index,
				       uint8_t count,
				       const struct bt_mesh_sensor_series_entry *entry)
{
	printk("Relative runtime in %s", bt_mesh_sensor_ch_str(&entry->value[1]));
	printk(" to %s degrees: ", bt_mesh_sensor_ch_str(&entry->value[2]));
	printk("%s percent\n", bt_mesh_sensor_ch_str(&entry->value[0]));
}

static void sensor_cli_setting_status_cb(struct bt_mesh_sensor_cli *cli,
					 struct bt_mesh_msg_ctx *ctx,
					 const struct bt_mesh_sensor_type *sensor,
					 const struct bt_mesh_sensor_setting_status *setting)
{
	printk("Sensor ID: 0x%04x, Setting ID: 0x%04x\n", sensor->id, setting->type->id);
	for (int chan = 0; chan < setting->type->channel_count; chan++) {
		printk("\tChannel %d value: %s\n", chan,
		       bt_mesh_sensor_ch_str(&(setting->value[chan])));
	}
}

static void sensor_cli_desc_cb(struct bt_mesh_sensor_cli *cli, struct bt_mesh_msg_ctx *ctx,
			       const struct bt_mesh_sensor_info *sensor)
{
	printk("Descriptor of sensor with ID 0x%04x:\n", sensor->id);
	printk("\ttolerance: { positive: %d negative: %d }\n",
	       sensor->descriptor.tolerance.positive, sensor->descriptor.tolerance.negative);
	printk("\tsampling type: %d\n", sensor->descriptor.sampling_type);
}

static const struct bt_mesh_sensor_cli_handlers bt_mesh_sensor_cli_handlers = {
	.data = sensor_cli_data_cb,
	.series_entry = sensor_cli_series_entry_cb,
	.setting_status = sensor_cli_setting_status_cb,
	.sensor = sensor_cli_desc_cb,
};

static struct bt_mesh_sensor_cli sensor_cli = BT_MESH_SENSOR_CLI_INIT(&bt_mesh_sensor_cli_handlers);

static struct k_work_delayable get_data_work;

#define RESPONSE_TIMEOUT_MS     5000


static void get_data(struct k_work *work)
{
    if (!bt_mesh_is_provisioned()) {
        /* not on the mesh yet? retry later */
        k_work_schedule(&get_data_work,
                        K_MSEC(GET_DATA_INTERVAL));
        return;
    }

    /* Persistent state across invocations */
    static uint32_t server_idx;   /* which server in server_addrs[] */
    static uint32_t sensor_idx;   /* which sensor in sensor_defs[] */
    static bool     printing;     /* are we in the print phase? */

    const size_t n_servers = ARRAY_SIZE(server_addrs);
    const size_t n_sensors = ARRAY_SIZE(sensor_defs);

    /* 1) POLLING PHASE */
    if (!printing) {
        /* first sensor of this server? clear flags & announce */
        if (sensor_idx == 0) {
            for (size_t s = 0; s < n_sensors; s++) {
                size_t idx = server_idx * n_sensors + s;
                sensor_table[idx].valid = false;
            }
            printk("\n=== Requesting SERVER 0x%04X DATA ===\n",
                   server_addrs[server_idx]);
        }

        /* build ctx & send one GET */
        {
            size_t idx = server_idx * n_sensors + sensor_idx;
            struct bt_mesh_msg_ctx *ctx = &sensor_table[idx].ctx;

            /* re-build ctx to point at this server’s element */
            ctx->net_idx  = NET_IDX;
            ctx->app_idx  = APP_IDX;
            ctx->addr     = server_addrs[server_idx]
                            + sensor_defs[sensor_idx].elem_offset;
            ctx->send_ttl = DEFAULT_TTL;

            printk("Requesting %s (0x%04X) at addr 0x%04X\n",
                   sensor_defs[sensor_idx].name,
                   sensor_defs[sensor_idx].type->id,
                   ctx->addr);

            bt_mesh_sensor_cli_get(&sensor_cli,
                                   ctx,
                                   sensor_defs[sensor_idx].type,
                                   NULL);
        }

        sensor_idx++;

        /* schedule next sensor GET, or the print phase */
        if (sensor_idx < n_sensors) {
            k_work_schedule(&get_data_work,
                            K_MSEC(GET_DATA_INTERVAL_QUICK));
        } else {
            /* all GETs sent for this server—wait for responses */
            printing = true;
            k_work_schedule(&get_data_work,
                            K_MSEC(RESPONSE_TIMEOUT_MS));
        }

        return;
    }

    /* 2) PRINTING PHASE */
    {
        uint32_t now = k_uptime_get_32();
        size_t   base = server_idx * n_sensors;

        /* CSV header once, if you like—optional */
        static uint32_t last_header;
        if (now - last_header > 10000) {
            printk("SERVER, timestamp_ms");
            for (size_t s = 0; s < n_sensors; s++) {
                printk(",%s", sensor_defs[s].name);
            }
            printk("\n");
            last_header = now;
        }

        /* CSV data row for this server */
        printk("0x%04X,%u",
               server_addrs[server_idx],
               (unsigned)now);
        for (size_t s = 0; s < n_sensors; s++) {
            size_t idx = base + s;
            if (sensor_table[idx].valid) {
                float vf = 0.0f;
                bt_mesh_sensor_value_to_float(&sensor_table[idx].value,
                                              &vf);
                printk(",%.2f", (double)vf);
            } else {
                printk(","); /* blank on timeout */
            }
        }
        printk("\n");
    }

    /* 3) ADVANCE TO NEXT SERVER */
    server_idx = (server_idx + 1) % n_servers;
    sensor_idx = 0;
    printing   = false;

    /* schedule next server’s cycle */
    k_work_schedule(&get_data_work,
                    K_MSEC(GET_DATA_INTERVAL));
}



static const int temp_ranges[][2] = {
	{0, 100},
	{10, 20},
	{22, 30},
	{40, 50},
};

static const int presence_motion_threshold[] = {0, 25, 50, 75, 100};

static int setting_set_int(const struct bt_mesh_sensor_type *sensor_type,
			   const struct bt_mesh_sensor_type *setting_type, const int *values)
{
	struct bt_mesh_sensor_value sensor_vals[CONFIG_BT_MESH_SENSOR_CHANNELS_MAX];
	int err;

	for (int i = 0; i < setting_type->channel_count; i++) {
		err = bt_mesh_sensor_value_from_micro(setting_type->channels[i].format,
						      values[i] * 1000000LL, &sensor_vals[i]);
		if (err) {
			return err;
		}
	}

	return bt_mesh_sensor_cli_setting_set(&sensor_cli, NULL, sensor_type, setting_type,
					      sensor_vals, NULL);
}

static void button_handler_cb(uint32_t pressed, uint32_t changed)
{
	if (!bt_mesh_is_provisioned()) {
		return;
	}

	static uint32_t temp_idx;
	static uint32_t motion_threshold_idx;
	int err;

	if (pressed & changed & BIT(0)) {
		err = bt_mesh_sensor_cli_setting_get(&sensor_cli, NULL,
						     &bt_mesh_sensor_present_dev_op_temp,
						     &bt_mesh_sensor_dev_op_temp_range_spec, NULL);
		if (err) {
			printk("Error getting range setting (%d)\n", err);
		}
	}
	if (pressed & changed & BIT(1)) {
		err = setting_set_int(&bt_mesh_sensor_present_dev_op_temp,
				      &bt_mesh_sensor_dev_op_temp_range_spec,
				      temp_ranges[temp_idx++]);
		if (err) {
			printk("Error setting range setting (%d)\n", err);
		}
		temp_idx = temp_idx % ARRAY_SIZE(temp_ranges);
	}
	if (pressed & changed & BIT(2)) {
		err = bt_mesh_sensor_cli_desc_get(&sensor_cli, NULL,
						  &bt_mesh_sensor_present_dev_op_temp, NULL);
		if (err) {
			printk("Error getting sensor descriptor (%d)\n", err);
		}
	}
	if (pressed & changed & BIT(3)) {
		err = setting_set_int(&bt_mesh_sensor_presence_detected,
				      &bt_mesh_sensor_motion_threshold,
				      &presence_motion_threshold[motion_threshold_idx++]);
		if (err) {
			printk("Error setting motion threshold setting (%d)\n", err);
		}
		motion_threshold_idx = motion_threshold_idx % ARRAY_SIZE(presence_motion_threshold);
	}
}

static struct button_handler button_handler = {
	.cb = button_handler_cb,
};

/* Set up a repeating delayed work to blink the DK's LEDs when attention is
 * requested.
 */
static struct k_work_delayable attention_blink_work;
static bool attention;

static void attention_blink(struct k_work *work)
{
	static int idx;
	const uint8_t pattern[] = {
		BIT(0) | BIT(1),
		BIT(1) | BIT(2),
		BIT(2) | BIT(3),
		BIT(3) | BIT(0),
	};

	if (attention) {
		dk_set_leds(pattern[idx++ % ARRAY_SIZE(pattern)]);
		k_work_reschedule(&attention_blink_work, K_MSEC(30));
	} else {
		dk_set_leds(DK_NO_LEDS_MSK);
	}
}

static void attention_on(const struct bt_mesh_model *mod)
{
	attention = true;
	k_work_reschedule(&attention_blink_work, K_NO_WAIT);
}

static void attention_off(const struct bt_mesh_model *mod)
{
	/* Will stop rescheduling blink timer */
	attention = false;
}

static const struct bt_mesh_health_srv_cb health_srv_cb = {
	.attn_on = attention_on,
	.attn_off = attention_off,
};

static struct bt_mesh_health_srv health_srv = {
	.cb = &health_srv_cb,
};

BT_MESH_HEALTH_PUB_DEFINE(health_pub, 0);

static struct bt_mesh_elem elements[] = {
	BT_MESH_ELEM(1,
		     BT_MESH_MODEL_LIST(BT_MESH_MODEL_CFG_SRV,
					BT_MESH_MODEL_HEALTH_SRV(&health_srv, &health_pub),
					BT_MESH_MODEL_SENSOR_CLI(&sensor_cli)),
		     BT_MESH_MODEL_NONE),
};

static const struct bt_mesh_comp comp = {
	.cid = CONFIG_BT_COMPANY_ID,
	.elem = elements,
	.elem_count = ARRAY_SIZE(elements),
};

const struct bt_mesh_comp *model_handler_init(void)
{
	k_work_init_delayable(&attention_blink_work, attention_blink);
	k_work_init_delayable(&get_data_work, get_data);
	k_work_init_delayable(&motion_timeout_work, motion_timeout);

	dk_button_handler_add(&button_handler);
	k_work_schedule(&get_data_work, K_MSEC(GET_DATA_INTERVAL));

    init_sensor_table();

	return &comp;
}
