#include <assert.h>
#include <math.h>

#include "array2f.h"
#include "resolution.h"

array2f create_array2f(resolution_t resolution) {
    array2f array;
    array.buffer = malloc(sizeof(float) * resolution_area(resolution));
    array.resolution = resolution;
    array.stride = resolution.width;
    array.owns_buffer = true;
    return array;
}

void destroy_array2f(const array2f *array) {
    if (array->owns_buffer) free(array->buffer);
}

float array2f_get(const array2f *array, size_t x, size_t y) {
    return array->buffer[y * array->stride + x];
}

void array2f_set(const array2f *array, size_t x, size_t y, float value) {
    array->buffer[y * array->stride + x] = value;
}

void array2f_filter(array2f *array, array2f_operator_t operator) {
    size_t index = 0;
    for (int y = 0; y < array->resolution.height; y++) {
        for (int x = 0; x < array->resolution.width; x++) {
            array->buffer[index] = operator(array->buffer[index]);
            index++;
        }
        index += (array->stride - array->resolution.width);
    }
}

// Sub-array by padding
array2f array2f_pad(const array2f *array, size_t pad_x, size_t pad_y) {
    array2f a;
    a.stride = array->stride;
    a.buffer = array->buffer + pad_y * a.stride + pad_x;
    a.resolution.width = array->resolution.width - 2 * pad_x;
    a.resolution.height = array->resolution.height - 2* pad_y;
    a.owns_buffer = false;
    return a;
}

size_t array2f_area(const array2f *array) {
    return resolution_area(array->resolution);
}

float array2f_high(const array2f *array) {
    float tmp = -INFINITY;
    size_t index = 0;
    for (int y = 0; y < array->resolution.height; y++) {
        for (int x = 0; x < array->resolution.width; x++) {
            if (array->buffer[index] > tmp) tmp = array->buffer[index];
            index++;
        }
        index += (array->stride - array->resolution.width);
    }
    return tmp;
}

float array2f_low(const array2f *array) {
    float tmp = INFINITY;
    size_t index = 0;
    for (int y = 0; y < array->resolution.height; y++) {
        for (int x = 0; x < array->resolution.width; x++) {
            if (array->buffer[index] < tmp) tmp = array->buffer[index];
            index++;
        }
        index += (array->stride - array->resolution.width);
    }
    return tmp;
}

void array2f_fill(array2f a, float value) {
    size_t c = 0;
    for (size_t y = 0; y < a.resolution.height; y++) {
        for (size_t x = 0; x < a.resolution.width; x++) {
            a.buffer[c++] = value;
        }
        c += (a.stride - a.resolution.width);
    }
}

void array2f_norm2(const array2f *u, const array2f *v, array2f *destination) {
    assert(resolution_equal(u->resolution, destination->resolution));
    assert(resolution_equal(v->resolution, destination->resolution));
    size_t di = 0, ui = 0, vi = 0;
    for (int y = 0; y < destination->resolution.height; y++) {
        for (int x = 0; x < destination->resolution.width; x++) {
            float uu = u->buffer[ui];
            float vv = v->buffer[vi];
            destination->buffer[di] = uu * uu + vv * vv;
            di++; ui++; vi++;
        }
        di += (destination->stride - destination->resolution.width);
        ui += (u->stride - u->resolution.width);
        vi += (v->stride - v->resolution.width);
    }
}