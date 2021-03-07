#include "array2f.h"

#define IX(i,j) ((i)+(N+2)*(j))
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

void set_bnd(int N, int b, const array2f *x)
{
	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;

	for (size_t i = 1; i < w - 1; i++) {
		ARRAY2F_AT(x, i, 0) = b==2 ? -ARRAY2F_AT(x, i,   1) : ARRAY2F_AT(x, i,   1);
		ARRAY2F_AT(x, i, h-1) = b==2 ? -ARRAY2F_AT(x, i, h-2) : ARRAY2F_AT(x, i, h-2);
	}
	for (size_t j = 1; j < h - 1; j++) {
		ARRAY2F_AT(x, 0  , j) = b==1 ? -ARRAY2F_AT(x, 1, j) : ARRAY2F_AT(x, 1, j);
		ARRAY2F_AT(x, w-1, j) = b==1 ? -ARRAY2F_AT(x, w-2, j) : ARRAY2F_AT(x, w-2, j);
	}
	ARRAY2F_AT(x, 0  ,0  ) = 0.5f*(ARRAY2F_AT(x, 1,0  )+ARRAY2F_AT(x, 0  ,1));
	ARRAY2F_AT(x, 0  ,h-1) = 0.5f*(ARRAY2F_AT(x, 1,h-1)+ARRAY2F_AT(x, 0  ,h-2));
	ARRAY2F_AT(x, w-1,0  ) = 0.5f*(ARRAY2F_AT(x, w-2,0  )+ARRAY2F_AT(x, w-1,1));
	ARRAY2F_AT(x, w-1,h-1) = 0.5f*(ARRAY2F_AT(x, w-2,h-1)+ARRAY2F_AT(x, w-1,h-2));
}

void lin_solve ( int N, int b, const array2f *x, const array2f *x0, float a, float c )
{
	const size_t w = x->resolution.width;
	const size_t h = x->resolution.height;

	for (size_t k = 0; k < 20; k++) {
		for (size_t j = 1; j < h - 1; j++) {
			for (size_t i = 1; i < w - 1; i++) {
				x->buffer[IX(i,j)] = (x0->buffer[IX(i,j)] + a*(x->buffer[IX(i-1,j)]+x->buffer[IX(i+1,j)]+x->buffer[IX(i,j-1)]+x->buffer[IX(i,j+1)]))/c;
			}
		}
	}
}

void diffuse(int N, int b, const array2f *x, const array2f *x0, float diff, float dt )
{
	float a = dt * diff * N * N;
	lin_solve( N, b, x, x0, a, 1 + 4 * a);
	set_bnd(N, b, x);
}

void advect( int N, int b, const array2f *d, const array2f *d0, const array2f *u, const array2f *v, float dt)
{
	int i0, j0, i1, j1;
	float x, y, s0, t0, s1, t1, dt0;

	const size_t w = d0->resolution.width;
	const size_t h = d0->resolution.height;

	dt0 = dt*N;
	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			x = i-dt0*u->buffer[IX(i,j)]; y = j-dt0*v->buffer[IX(i,j)];
			if (x<0.5f) x=0.5f;
			if (x>N+0.5f) x=N+0.5f;
			i0=(int)x; i1=i0+1;
			if (y<0.5f) y=0.5f;
			if (y>N+0.5f) y=N+0.5f;
			j0=(int)y; j1=j0+1;
			s1 = x-i0; s0 = 1-s1; t1 = y-j0; t0 = 1-t1;
			d->buffer[IX(i,j)] = s0*(t0*d0->buffer[IX(i0,j0)]+t1*d0->buffer[IX(i0,j1)])+
								s1*(t0*d0->buffer[IX(i1,j0)]+t1*d0->buffer[IX(i1,j1)]);
		}
	}
	set_bnd(N, b, d);
}

void project(int N, const array2f *u, const array2f *v, const array2f *p, const array2f *div)
{
	const size_t w = u->resolution.width;
	const size_t h = u->resolution.height;

	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			div->buffer[IX(i,j)] = -0.5f*(u->buffer[IX(i+1,j)]-u->buffer[IX(i-1,j)]+v->buffer[IX(i,j+1)]-v->buffer[IX(i,j-1)])/N;
			p->buffer[IX(i,j)] = 0;
		}
	}
	set_bnd(N, 0, div); set_bnd( N, 0, p);

	lin_solve(N, 0, p, div, 1, 4);
	set_bnd(N, 0, p);

	for (size_t j = 1; j < h - 1; j++) {
		for (size_t i = 1; i < w - 1; i++) {
			u->buffer[IX(i,j)] -= 0.5f*N*(p->buffer[IX(i+1,j)]-p->buffer[IX(i-1,j)]);
			v->buffer[IX(i,j)] -= 0.5f*N*(p->buffer[IX(i,j+1)]-p->buffer[IX(i,j-1)]);
		}
	}
	set_bnd(N, 1, u); set_bnd(N, 2, v);
}

void density_step(size_t N, array2f *x, array2f *x0, array2f *u, array2f *v, float diff, float dt)
{
	add_source(x, x0, dt);
	SWAP ( x0, x ); diffuse( N, 0, x, x0, diff, dt );
	SWAP ( x0, x ); advect ( N, 0, x, x0, u, v, dt );
}

void velocity_step(size_t N, array2f *u, array2f *v, array2f *u0, array2f *v0, float visc, float dt)
{
	add_source(u, u0, dt); add_source(v, v0, dt);
	SWAP ( u0, u ); diffuse(N, 1, u, u0, visc, dt);
	SWAP ( v0, v ); diffuse(N, 2, v, v0, visc, dt);
	project ( N, u, v, u0, v0 );
	SWAP ( u0, u ); SWAP ( v0, v );
	advect ( N, 1, u, u0, u0, v0, dt);
	advect ( N, 2, v, v0, u0, v0, dt);
	project ( N, u, v, u0, v0 );
}
