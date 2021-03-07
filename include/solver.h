#ifndef _SOLVER_H
#define _SOLVER_H

void density_step(int N, float * x, float * x0, float * u, float * v, float diff, float dt);
void velocity_step(int N, float * u, float * v, float * u0, float * v0, float visc, float dt);

#endif