#include "xf.h"
#include "solver.h"
#include "array2f.h"

#define SWAP(x0,x) {array2f * tmp=x0;x0=x;x=tmp;}

void add_source(const array2f *array, const array2f *source, float dt )
{
	for (size_t y = 0; y < array->resolution.height; y++) {
		for (size_t x = 0; x < array->resolution.width; x++) {
			array2f_set(
				array, x, y,
				array2f_get(array, x, y) + array2f_get(source, x, y) * dt);
		}
	}
}

void set_neutral_edges(const array2f *x) {
	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;
	for (size_t j = 0; j < h; j++) {
		ARRAY2F_AT(x, 0, j) = array2f_get(x, 1, j);
		ARRAY2F_AT(x, w - 1, j) = array2f_get(x, w - 2, j);
	}
	for (size_t i = 0; i < w; i++) {
		ARRAY2F_AT(x, i, 0) = array2f_get(x, i, 1);
		ARRAY2F_AT(x, i, h - 1) = array2f_get(x, i, h - 2);
	}
}

void mirror_bnd(const array2f *x, const array2f *m, int dx, int dy) {
	// Always set the edges to closest value
	set_neutral_edges(x);

	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;
	for (size_t j = 0; j < h; j++) {
		for (size_t i = 0; i < w; i++) {
			const float d = array2f_get(m, i, j);
			const int di = signf(d);
			array2f_set(x, i, j,
				lerpf(array2f_get(x, i, j), -array2f_get(x, i + dx * di, j + dy * di), abs(d)));
		}
	}
}

void set_bnd(const array2f *x, const bounds_t *bounds)
{
	// Always set the edges to closest value
	set_neutral_edges(x);

	// Check dynamic boundaries
	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;
	for (size_t j = 0; j < h; j++) {
		for (size_t i = 0; i < w; i++) {
			const float dx = array2f_get(&bounds->bx, i, j);
			const float dy = array2f_get(&bounds->by, i, j);
			const int dxi = signf(dx);
			const int dyi = signf(dy);
			array2f_set(x, i, j, array2f_get(x, i + dxi, j + dyi));
		}
	}
}

void lin_solve(const array2f *x, const array2f *x0, float a, float c)
{
	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;

	for (size_t k = 0; k < 20; k++) {
		for (size_t j = 1; j < h - 1; j++) {
			for (size_t i = 1; i < w - 1; i++) {
				ARRAY2F_AT(x, i, j) = (array2f_get(x0, i,j) + a * (
					array2f_get(x, i - 1, j) +
					array2f_get(x, i + 1, j) +
					array2f_get(x, i, j - 1) +
					array2f_get(x, i, j + 1))) / c;
			}
		}
	}
}

void diffuse(const array2f *x, const array2f *x0, float diff, float dt )
{
	float a = dt * diff * array2f_area(x);
	lin_solve(x, x0, a, 1 + 4 * a);
}

void advect(const array2f *d, const array2f *d0, const array2f *u, const array2f *v, float dt)
{
	const size_t w = d0->resolution.width;
	const size_t h = d0->resolution.height;

	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			float x = i - (dt * (w - 2)) * array2f_get(u, i, j);
			if (x < 0.5f) x = 0.5f;
			if (x > w-2 + 0.5f) x = w-2 + 0.5f;

			float y = j - (dt * (h - 2)) * array2f_get(v, i, j);
			if (y < 0.5f) y = 0.5f;
			if (y > h-2+0.5f) y = h-2 + 0.5f;
			
			size_t i0=(int)x, i1 = i0 + 1;
			size_t j0=(int)y, j1 = j0 + 1;

			float s1 = x - i0, s0 = 1 - s1;
			float t1 = y - j0, t0 = 1 - t1;
			ARRAY2F_AT(d, i, j) =
				s0 * (t0 * array2f_get(d0, i0, j0) + t1 * array2f_get(d0, i0, j1)) +
				s1 * (t0 * array2f_get(d0, i1, j0) + t1 * array2f_get(d0, i1, j1));
		}
	}
}

void project(const array2f *u, const array2f *v, const array2f *p, const array2f *divergence, const bounds_t *bounds)
{
	const size_t w = u->resolution.width;
	const size_t h = u->resolution.height;

	const size_t N = (w + h - 4) / 2; // TODO: Should this be sqrt instead?
	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			ARRAY2F_AT(divergence, i, j) = -0.5f * (
				array2f_get(u, i + 1, j) - array2f_get(u, i - 1, j) +
				array2f_get(v, i, j + 1) - array2f_get(v, i, j - 1)) / N;
			ARRAY2F_AT(p, i, j) = 0;
		}
	}
	set_bnd(divergence, bounds); set_bnd(p, bounds);

	lin_solve(p, divergence, 1, 4);
	set_bnd(p, bounds);

	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			ARRAY2F_AT(u, i, j) -= 0.5f * (w-2) * (array2f_get(p, i + 1, j) - array2f_get(p, i - 1, j));
			ARRAY2F_AT(v, i, j) -= 0.5f * (h-2) * (array2f_get(p, i, j + 1) - array2f_get(p, i, j - 1));
		}
	}
	mirror_bnd(u, &bounds->bx, 1, 0); mirror_bnd(v, &bounds->by, 0, 1);
}

void density_step(array2f *x, array2f *x0, array2f *u, array2f *v, const bounds_t *bounds, float diffusion, float dt)
{
	add_source(x, x0, dt);
	SWAP(x0, x); diffuse(x, x0, diffusion, dt); set_bnd(x, bounds);
	SWAP(x0, x); advect(x, x0, u, v, dt); set_bnd(x, bounds);
}

void velocity_step(array2f *u, array2f *v, array2f *u0, array2f *v0, const bounds_t *bounds, float viscosity, float dt)
{
	add_source(u, u0, dt); add_source(v, v0, dt);
	SWAP(u0, u); diffuse(u, u0, viscosity, dt); mirror_bnd(u, &bounds->bx, 1, 0);

	SWAP(v0, v); diffuse(v, v0, viscosity, dt); mirror_bnd(v, &bounds->by, 0, 1);

	project(u, v, u0, v0, bounds);
	SWAP(u0, u); SWAP(v0, v);
	advect(u, u0, u0, v0, dt); mirror_bnd(u, &bounds->bx, 1, 0);
	advect(v, v0, u0, v0, dt); mirror_bnd(v, &bounds->by, 0, 1);

	project(u, v, u0, v0, bounds);
}
