#include "array2f.h"
#include "resolution.h"

array2f create_array2f(size_t width, size_t height) {
    array2f array;
    array.buffer = malloc(sizeof(float) * width * height);
    array.resolution.width = width;
    array.resolution.height = height;
    array.stride = width;
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