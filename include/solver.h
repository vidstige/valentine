#ifndef _SOLVER_H
#define _SOLVER_H

#include <stdlib.h>
#include "array2f.h"

void density_step(size_t N, array2f *x, array2f *x0, array2f *u, array2f *v, float diff, float dt);
void velocity_step(size_t N, array2f *u, array2f *v, array2f *u0, array2f *v0, float visc, float dt);

#endif