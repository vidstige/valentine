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

float dirty_mirror(int b, int dx, int dy) {
	if (b == 1 && dx == 0) {
		return -1.0f;
	}
	if (b == 2 && dy == 0) {
		return -1.0f;
	}
	return 1.0f;
}

void set_bnd(int b, const array2f *x, const bounds_t *bounds)
{
	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;

	// Always set the edges to closest value
	for (size_t j = 0; j < h; j++) {
		ARRAY2F_AT(x, 0, j) = array2f_get(x, 1, j);
		ARRAY2F_AT(x, w - 1, j) = array2f_get(x, w - 2, j);
	}
	for (size_t i = 0; i < w; i++) {
		ARRAY2F_AT(x, i, 0) = array2f_get(x, i, 1);
		ARRAY2F_AT(x, i, h - 1) = array2f_get(x, i, h - 2);
	}

	// Check dynamic boundaries
	array2f tmp = create_array2f(x->resolution.width, x->resolution.height);
	for (size_t j = 0; j < h; j++) {
		for (size_t i = 0; i < w; i++) {
			int dx = (int)array2f_get(&bounds->bx, i, j);
			int dy = (int)array2f_get(&bounds->by, i, j);
			float m = dirty_mirror(b, dx, dy);
			array2f_set(&tmp, i, j,
				m * array2f_get(x, i + dx, j + dy)
			);
		}
	}
	
	for (size_t j = 0; j < h; j++) {
		for (size_t i = 0; i < w; i++) {
			array2f_set(x, i, j, array2f_get(&tmp, i, j));
		}
	}
	destroy_array2f(&tmp);
/*
	for (size_t i = 1; i < w - 1; i++) {
		ARRAY2F_AT(x, i, 0) = b==2 ? -array2f_get(x, i, 1) : array2f_get(x, i,   1);
		ARRAY2F_AT(x, i, h - 1) = b==2 ? -array2f_get(x, i, h - 2) : array2f_get(x, i, h - 2);
	}
	for (size_t j = 1; j < h - 1; j++) {
		ARRAY2F_AT(x, 0, j) = b==1 ? -array2f_get(x, 1, j) : array2f_get(x, 1, j);
		ARRAY2F_AT(x, w - 1, j) = b==1 ? -array2f_get(x, w - 2, j) : array2f_get(x, w - 2, j);
	}
*/
	/*ARRAY2F_AT(x, 0, 0) = 0.5f*(array2f_get(x, 1, 0) + array2f_get(x, 0, 1));
	ARRAY2F_AT(x, 0, h - 1) = 0.5f*(array2f_get(x, 1, h - 1) + array2f_get(x, 0, h - 2));
	ARRAY2F_AT(x, w - 1, 0) = 0.5f*(array2f_get(x, w - 2, 0  ) + array2f_get(x, w - 1, 1));
	ARRAY2F_AT(x, w - 1, h - 1) = 0.5f*(array2f_get(x, w - 2, h - 1) + array2f_get(x, w - 1, h - 2));*/
}

void lin_solve(int b, const array2f *x, const array2f *x0, float a, float c)
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

void diffuse(int b, const array2f *x, const array2f *x0, const bounds_t *bounds, float diff, float dt )
{
	float a = dt * diff * array2f_area(x);
	lin_solve(b, x, x0, a, 1 + 4 * a);
	set_bnd(b, x, bounds);
}

void advect(int b, const array2f *d, const array2f *d0, const array2f *u, const array2f *v, const bounds_t *bounds, float dt)
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
			ARRAY2F_AT(d, i, j) = s0 * (t0 * array2f_get(d0, i0, j0) + t1 * array2f_get(d0, i0, j1)) +
								  s1 * (t0 * array2f_get(d0, i1, j0) + t1 * array2f_get(d0, i1, j1));
		}
	}
	set_bnd(b, d, bounds);
}

void project(const array2f *u, const array2f *v, const array2f *p, const array2f *div, const bounds_t *bounds)
{
	const size_t w = u->resolution.width;
	const size_t h = u->resolution.height;

	const size_t N = (w + h - 4) / 2; // TODO: Should this be sqrt instead?
	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			ARRAY2F_AT(div, i, j) = -0.5f * (
				array2f_get(u, i + 1, j) - array2f_get(u, i - 1, j) +
				array2f_get(v, i, j + 1) - array2f_get(v, i, j - 1)) / N;
			ARRAY2F_AT(p, i, j) = 0;
		}
	}
	set_bnd(0, div, bounds); set_bnd(0, p, bounds);

	lin_solve(0, p, div, 1, 4);
	set_bnd(0, p, bounds);

	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			ARRAY2F_AT(u, i, j) -= 0.5f * (w-2) * (array2f_get(p, i + 1, j) - array2f_get(p, i - 1, j));
			ARRAY2F_AT(v, i, j) -= 0.5f * (h-2) * (array2f_get(p, i, j + 1) - array2f_get(p, i, j - 1));
		}
	}
	set_bnd(1, u, bounds); set_bnd(2, v, bounds);
}

void density_step(array2f *x, array2f *x0, array2f *u, array2f *v, const bounds_t *bounds, float diff, float dt)
{
	add_source(x, x0, dt);
	SWAP(x0, x); diffuse(0, x, x0, bounds, diff, dt);
	SWAP(x0, x); advect (0, x, x0, u, v, bounds, dt);
}

void velocity_step(array2f *u, array2f *v, array2f *u0, array2f *v0, const bounds_t *bounds, float visc, float dt)
{
	add_source(u, u0, dt); add_source(v, v0, dt);
	SWAP(u0, u); diffuse(1, u, u0, bounds, visc, dt);
	SWAP(v0, v); diffuse(2, v, v0, bounds, visc, dt);
	project(u, v, u0, v0, bounds);
	SWAP(u0, u); SWAP(v0, v);
	advect(1, u, u0, u0, v0, bounds, dt);
	advect(2, v, v0, u0, v0, bounds, dt);
	project(u, v, u0, v0, bounds);
}
