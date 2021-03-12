#ifndef _COLORMAP_H
#define _COLORMAP_H

#include <stdlib.h>
#include "color.h"

typedef struct {
    size_t count;
    color_t *colors;
} colormap_t;

colormap_t create_colormap(size_t count, ...);
void destroy_colormap(const colormap_t *colormap);
color_t colormap_get(const colormap_t *colormap, float t);

#endif