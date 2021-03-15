#include "xf.h"

// returns -1, -1 depending on the sign of x. For x=+0 or -0 return 0
int signf(float x) {
	return (x > 0) - (x < 0);
}

float lerpf(float a, float b, float t) {
	return a * (1 - t) + b * t;
}

float clampf(float x, float lo, float hi) {
    if (x < lo) return lo;
    if (x > hi) return hi;
    return x;
}