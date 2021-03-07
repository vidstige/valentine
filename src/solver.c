#include "array2f.h"

#define IX(i,j) ((i)+(N+2)*(j))
#define SWAP(x0,x) {array2f * tmp=x0;x0=x;x=tmp;}
#define FOR_EACH_CELL for ( i=1 ; i<=N ; i++ ) { for ( j=1 ; j<=N ; j++ ) {
#define END_FOR }}

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

void set_bnd(int N, int b, float * x)
{
	int i;

	for ( i=1 ; i<=N ; i++ ) {
		x[IX(0  ,i)] = b==1 ? -x[IX(1,i)] : x[IX(1,i)];
		x[IX(N+1,i)] = b==1 ? -x[IX(N,i)] : x[IX(N,i)];
		x[IX(i,0  )] = b==2 ? -x[IX(i,1)] : x[IX(i,1)];
		x[IX(i,N+1)] = b==2 ? -x[IX(i,N)] : x[IX(i,N)];
	}
	x[IX(0  ,0  )] = 0.5f*(x[IX(1,0  )]+x[IX(0  ,1)]);
	x[IX(0  ,N+1)] = 0.5f*(x[IX(1,N+1)]+x[IX(0  ,N)]);
	x[IX(N+1,0  )] = 0.5f*(x[IX(N,0  )]+x[IX(N+1,1)]);
	x[IX(N+1,N+1)] = 0.5f*(x[IX(N,N+1)]+x[IX(N+1,N)]);
}

void lin_solve ( int N, int b, float * x, float * x0, float a, float c )
{
	int i, j, k;

	for (size_t k = 0; k < 20; k++) {
		FOR_EACH_CELL
			x[IX(i,j)] = (x0[IX(i,j)] + a*(x[IX(i-1,j)]+x[IX(i+1,j)]+x[IX(i,j-1)]+x[IX(i,j+1)]))/c;
		END_FOR
	}
}

void diffuse(int N, int b, const array2f *x, const array2f *x0, float diff, float dt )
{
	float a = dt * diff * N * N;
	lin_solve( N, b, x->buffer, x0->buffer, a, 1 + 4 * a);
	set_bnd(N, b, x->buffer);
}

void advect ( int N, int b, float * d, float * d0, float * u, float * v, float dt )
{
	int i, j, i0, j0, i1, j1;
	float x, y, s0, t0, s1, t1, dt0;

	dt0 = dt*N;
	FOR_EACH_CELL
		x = i-dt0*u[IX(i,j)]; y = j-dt0*v[IX(i,j)];
		if (x<0.5f) x=0.5f;
		if (x>N+0.5f) x=N+0.5f;
		i0=(int)x; i1=i0+1;
		if (y<0.5f) y=0.5f;
		if (y>N+0.5f) y=N+0.5f;
		j0=(int)y; j1=j0+1;
		s1 = x-i0; s0 = 1-s1; t1 = y-j0; t0 = 1-t1;
		d[IX(i,j)] = s0*(t0*d0[IX(i0,j0)]+t1*d0[IX(i0,j1)])+
					 s1*(t0*d0[IX(i1,j0)]+t1*d0[IX(i1,j1)]);
	END_FOR
	set_bnd ( N, b, d );
}

void project(int N, const array2f *u, const array2f *v, const array2f *p, const array2f *div)
{
	int i, j;

	FOR_EACH_CELL
		div->buffer[IX(i,j)] = -0.5f*(u->buffer[IX(i+1,j)]-u->buffer[IX(i-1,j)]+v->buffer[IX(i,j+1)]-v->buffer[IX(i,j-1)])/N;
		p->buffer[IX(i,j)] = 0;
	END_FOR	
	set_bnd ( N, 0, div->buffer ); set_bnd ( N, 0, p->buffer );

	lin_solve ( N, 0, p->buffer, div->buffer, 1, 4 );
	set_bnd ( N, 0, p->buffer );

	FOR_EACH_CELL
		u->buffer[IX(i,j)] -= 0.5f*N*(p->buffer[IX(i+1,j)]-p->buffer[IX(i-1,j)]);
		v->buffer[IX(i,j)] -= 0.5f*N*(p->buffer[IX(i,j+1)]-p->buffer[IX(i,j-1)]);
	END_FOR
	set_bnd ( N, 1, u->buffer ); set_bnd ( N, 2, v->buffer );
}

void density_step(size_t N, array2f *x, array2f *x0, array2f *u, array2f *v, float diff, float dt)
{
	add_source(x, x0, dt);
	SWAP ( x0, x ); diffuse( N, 0, x, x0, diff, dt );
	SWAP ( x0, x ); advect ( N, 0, x->buffer, x0->buffer, u->buffer, v->buffer, dt );
}

void velocity_step(size_t N, array2f *u, array2f *v, array2f *u0, array2f *v0, float visc, float dt)
{
	add_source(u, u0, dt); add_source(v, v0, dt);
	SWAP ( u0, u ); diffuse(N, 1, u, u0, visc, dt);
	SWAP ( v0, v ); diffuse(N, 2, v, v0, visc, dt);
	project ( N, u, v, u0, v0 );
	SWAP ( u0, u ); SWAP ( v0, v );
	advect ( N, 1, u->buffer, u0->buffer, u0->buffer, v0->buffer, dt);
	advect ( N, 2, v->buffer, v0->buffer, u0->buffer, v0->buffer, dt);
	project ( N, u, v, u0, v0 );
}
