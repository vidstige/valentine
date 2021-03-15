#ifndef _ARRAY2F_H
#define _ARRAY2F_H

#include <stdbool.h>
#include <stdlib.h>
#include "resolution.h"

// array 2f
typedef struct {
    float *buffer;
    resolution_t resolution;
    size_t stride;
    bool owns_buffer;  // wether destroy should free the buffer
} array2f;

#define ARRAY2F_AT(array, x, y) (array)->buffer[(x) + (array)->stride * (y)]

typedef float (*array2f_operator_t)(float);

void array2f_filter(array2f *array, array2f_operator_t operator);

array2f create_array2f(resolution_t resolution);
void destroy_array2f(const array2f *array);
float array2f_get(const array2f *array, size_t x, size_t y);
void array2f_set(const array2f *array, size_t x, size_t y, float value);
array2f array2f_pad(const array2f *array, size_t pad_x, size_t pad_y);
size_t array2f_area(const array2f *array);
void array2f_fill(array2f a, float value);

#endif