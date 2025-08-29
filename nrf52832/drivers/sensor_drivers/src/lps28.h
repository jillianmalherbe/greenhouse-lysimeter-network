#ifndef _LPS28_H_
#define _LPS28_H_

#include <zephyr/types.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 
 * This struct holds both temperature (°C) and pressure (hPa). 
 */
struct lps28_data {
    float temp_c;
    float press_hpa;
};

/* 
 * Initialize the LPS28 sensor over I²C.
 * Returns 0 on success, or a negative error code.
 */
int lps28_init(void);

/*
 * Trigger a one‐shot measurement, wait for data ready,
 * read raw temperature + pressure, convert to floats, and
 * write into *data. 
 *
 * Returns 0 on success, or a negative error code.
 */
int lps28_fetch(struct lps28_data *data);

#ifdef __cplusplus
}
#endif

#endif /* _LPS28_H_ */

