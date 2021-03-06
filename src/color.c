#include <stdint.h>
#include <stdlib.h>

#include "color.h"

color_t rgb(uint32_t r, uint32_t g, uint32_t b) {
    const uint32_t alpha = 0xff;
    return alpha << 24 | (r & 0xff) << 16 | (g & 0xff) << 8 | (b & 0xff);
}

color_t rgbf(float r, float g, float b) {
    return rgb((uint32_t)(r * 255), (uint32_t)(g * 255), (uint32_t)(b * 255));
}

size_t get_alpha(color_t color) {
    return (color >> 24) & 0xff; 
}

color_t blend_color(color_t c1, color_t c2) {
    uint32_t c1_b = c1 & 0xff;
    uint32_t c1_g = (c1 >> 8) & 0xff;
    uint32_t c1_r = (c1 >> 16) & 0xff;

    uint32_t c2_b = c2 & 0xff;
    uint32_t c2_g = (c2 >> 8) & 0xff;
    uint32_t c2_r = (c2 >> 16) & 0xff;
    uint32_t a = (c2 >> 24) & 0xff;
    
    uint32_t ia = 0xff - a;
    //a = 0xff;
    //const ia = 0;
    return rgb(
        (c1_r * ia + c2_r * a) >> 8,
        (c1_g * ia + c2_g * a) >> 8,
        (c1_b * ia + c2_b * a) >> 8
    );
}