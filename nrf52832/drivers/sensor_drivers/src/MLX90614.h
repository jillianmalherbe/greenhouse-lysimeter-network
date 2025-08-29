/* MLX90614.h */
#ifndef MLX90614_H_
#define MLX90614_H_

#include <zephyr/types.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Returned data struct */
struct mlx90614_data {
    double ambient;   /* °C */
    double object;    /* °C */
};

/**
 * @brief Initialize MLX90614 driver
 *
 * @return 0 on success, -ENODEV if I2C bus not ready
 */
int mlx90614_init(void);

/**
 * @brief Read ambient and object temperatures
 *
 * @param data Pointer to struct to hold results
 * @return 0 on success, -EINVAL if data==NULL,
 *         -EIO on I2C error or invalid raw reading
 */
int mlx90614_fetch(struct mlx90614_data *data);

#ifdef __cplusplus
}
#endif

#endif /* MLX90614_H_ */


