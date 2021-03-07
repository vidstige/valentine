#ifndef _ARRAY2F_H
#define _ARRAY2F_H

#include <stdlib.h>
#include "resolution.h"

// array 2f
typedef struct {
    float *buffer;
    resolution_t resolution;
    size_t stride;
} array2f;


array2f create_array2f(size_t width, size_t height);
void destroy_array2f(const array2f *array);
float array2f_get(const array2f *array, size_t x, size_t y);
void array2f_set(const array2f *array, size_t x, size_t y, float value);
array2f array2f_pad(const array2f *array, size_t pad_x, size_t pad_y);

#endif