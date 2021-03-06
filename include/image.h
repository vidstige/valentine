#ifndef _IMAGE_H
#define _IMAGE_H

#include <stdint.h>
#include <stdlib.h>


typedef struct {
    size_t width;
    size_t height;
} resolution_t;

typedef struct {
    color_t* buffer;
    resolution_t resolution;
    size_t stride;
} image;

typedef struct {
    size_t x;
    size_t y;
} position_t;


image create_image(size_t width, size_t height);
void destroy_image(const image *image);
size_t image_pixel_count(const image *image);
size_t image_width(const image *image);
size_t image_height(const image *image);
color_t image_pixel(const image *image, size_t x, size_t y);

void clear(const image *image, color_t color);

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

// Sub-array by padding
array2f array2f_pad(const array2f *array, size_t pad_x, size_t pad_y);

#endif
