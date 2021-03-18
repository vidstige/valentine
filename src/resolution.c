#include <assert.h>
#include "resolution.h"

bool resolution_equal(resolution_t a, resolution_t b) {
    return a.width == b.width && a.height == b.height;
}

resolution_t resolution_same(resolution_t a, resolution_t b) {
    assert(resolution_equal(a, b));
    return a;
}

size_t resolution_area(resolution_t resolution) {
    return resolution.width * resolution.height;
}

