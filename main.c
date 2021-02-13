#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "./solver.h"

#ifndef M_PI
#    define M_PI 3.14159265358979323846
#endif

const size_t WIDTH = 506;
const size_t HEIGHT = 253;

void clear(uint32_t *buffer, uint32_t color) {
    size_t i;
    for (i = 0; i < WIDTH * HEIGHT; i++) {
        buffer[i] = color;
    }
}

uint32_t rgb(uint32_t r, uint32_t g, uint32_t b) {
    const uint32_t alpha = 0xff;
    return alpha << 24 | (r & 0xff) << 16 | (g & 0xff) << 8 | (b & 0xff);
}

uint32_t rgbf(float r, float g, float b) {
    return rgb((uint32_t)(r * 255), (uint32_t)(g * 255), (uint32_t)(b * 255));
}

float highf(float* array, size_t n) {
    float tmp = -INFINITY;
    for (size_t i = 0; i < n; i++) {
        if (array[i] > tmp) tmp = array[i];
    }
    return tmp;
}
float lowf(float* array, size_t n) {
    float tmp = INFINITY;
    for (size_t i = 0; i < n; i++) {
        if (array[i] < tmp) tmp = array[i];
    }
    return tmp;
}

void draw_dens(uint32_t *buffer, size_t N, float *dens) {
    const size_t size=(N+2)*(N+2);
    float hi = highf(dens, size);
    float lo = lowf(dens, size);
    for (size_t y = 0; y < HEIGHT; y++) {
        for (size_t x = 0; x < WIDTH; x++) {
            size_t dx = x * N / WIDTH + 1;
            size_t dy = y * N / HEIGHT + 1;
            float d = dens[dx + dy * (N + 2)];
            uint32_t intensity = (uint32_t)(255.0f*(d - lo / (hi - lo)));
            buffer[x + y * WIDTH] = rgbf(intensity, intensity, intensity);
        }
    }
}

void load_rgba(uint32_t *buffer, size_t width, size_t height, const char* filename) {
    FILE *fp;
    fp = fopen(filename,"w");
    if (!fp) {
        fprintf(stderr, "Could not open '%s': %s\n", filename, strerror(errno));
        exit(-1);
    }
    fread(buffer, sizeof(uint32_t), width*height, fp);
    fclose(fp);
}

int main() {
    uint32_t buffer[WIDTH * HEIGHT];
    const size_t N = 100;
    const size_t size=(N+2)*(N+2);
    float u[size], v[size], u_prev[size], v_prev[size];
    float dens[size], dens_prev[size]; 
    const float visc = 1, diff = 1;
    const float dt = 0.1;
    uint32_t img[N * N];
    load_rgba(img, N, N, "hearth.rgba");
    for (size_t frame = 0; frame < 1000; frame++) {
        //clear(buffer, 0xff222222);
        //get_from_UI ( dens_prev, u_prev, v_prev );
        vel_step(N, u, v, u_prev, v_prev, visc, dt);
        dens_step(N, dens, dens_prev, u, v, diff, dt);
        draw_dens(buffer, N, dens);
        fwrite(buffer, sizeof(uint32_t), WIDTH * HEIGHT, stdout);
    }
}