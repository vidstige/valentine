#ifndef _IMAGE_H
#define _IMAGE_H

#include <stdint.h>
#include <stdlib.h>

#include "color.h"
#include "resolution.h"

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
void image_scale(const image *target, const image *source);

#endif
