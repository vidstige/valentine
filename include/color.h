#ifndef _COLOR_H
#define _COLOR_H

#include <stdint.h>

typedef uint32_t color_t;
color_t blend_color(color_t c1, color_t c2);
color_t rgb(uint32_t r, uint32_t g, uint32_t b);
color_t rgbf(float r, float g, float b);
size_t get_alpha(color_t color);

#endif