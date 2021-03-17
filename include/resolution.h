#ifndef _RESOLUTION_H
#define _RESOLUTION_H

#include <stdbool.h>
#include <stdlib.h>

typedef struct {
    size_t width;
    size_t height;
} resolution_t;

bool resolution_equal(resolution_t a, resolution_t b);
size_t resolution_area(resolution_t resolution);

#endif

