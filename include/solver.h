#ifndef _SOLVER_H
#define _SOLVER_H

#include <stdlib.h>
#include "array2f.h"

typedef struct {
    array2f bx;
    array2f by;
} bounds_t;

void density_step(array2f *x, array2f *x0, array2f *u, array2f *v, const bounds_t *bounds, float diff, float dt);
void velocity_step(array2f *u, array2f *v, array2f *u0, array2f *v0, const bounds_t *bounds, float visc, float dt);

#endif