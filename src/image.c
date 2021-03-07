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
