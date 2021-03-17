#include "colormap.h"
#include <stdarg.h>

colormap_t create_colormap(size_t count, ...) {
  va_list args;
  colormap_t colormap;
  colormap.count = count;
  colormap.colors = malloc(sizeof(color_t) * count);
  va_start(args, count);
  for (size_t i = 0; i < count; i++) {
      colormap.colors[i] = va_arg(args, color_t);
  }
  va_end(args);
  return colormap;
}

void destroy_colormap(const colormap_t *colormap) {
    free(colormap->colors);
}

color_t colormap_get(const colormap_t *colormap, float t) {
    // |   |   |   |
    if (t < 0.f) t = 0.f;
    if (t > 1.f) t = 1.f;

    float size = 1.0f / (float)(colormap->count - 1);
    size_t i;
    for (i = 0; i < colormap->count - 1; i++) {
        if ((i+1) * size > t) break;
    }
    t -= i * size;
    t /= size;
    return lerp_color(colormap->colors[i], colormap->colors[i + 1], t);
}

