#include <stdint.h>
#include <stdlib.h>

#include "color.h"
#include "image.h"

image create_image(size_t width, size_t height) {
    image image;
    image.buffer = malloc(sizeof(color_t) * width * height);
    image.resolution.width = width;
    image.resolution.height = height;
    image.stride = width;
    return image;
}

void destroy_image(const image *image) {
    free(image->buffer);
}

size_t image_pixel_count(const image *image) {
    return image->resolution.width * image->resolution.height;
}
size_t image_width(const image *image) {
    return image->resolution.width;
}
size_t image_height(const image *image) {
    return image->resolution.height;
}
color_t image_pixel(const image *image, size_t x, size_t y) {
    return image->buffer[y * image->stride + x];
}

void clear(const image *image, color_t color) {
    size_t i;
    for (i = 0; i < image_pixel_count(image); i++) {
        image->buffer[i] = color;
    }
}

// array 2f

array2f create_array2f(size_t width, size_t height) {
    array2f array;
    array.buffer = malloc(sizeof(float) * width * height);
    array.resolution.width = width;
    array.resolution.height = height;
    array.stride = width;
    return array;
}

void destroy_array2f(const array2f *array) {
    free(array->buffer);
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
    return a;
}