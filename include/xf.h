#ifndef _XF_H
#define _XF_H

/** 
 * Floating point functions
 */

// returns -1, -1 depending on the sign of x. For x=+0 or -0 return 0
int signf(float x);

// Linear interpolation of two floats, depending on the weight t between 0 and 1.
float lerpf(float a, float b, float t);

float clampf(float x, float lo, float hi);

#endif

