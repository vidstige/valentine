#include <assert.h>
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

typedef uint32_t color_t;

typedef struct {
    size_t width;
    size_t height;
} resolution_t;

typedef struct {
    color_t* buffer;
    resolution_t resolution;
    size_t stride;
} image;

typedef struct {
    size_t x;
    size_t y;
} position_t;

size_t image_pixel_count(const image *image) {
    return image->resolution.width * image->resolution.height;
}
size_t image_width(const image *image) {
    return image->resolution.width;
}
size_t image_height(const image *image) {
    return image->resolution.height;
}
color_t image_pixel(const image *image, size_t x, size_t y) {
    return image->buffer[y * image->stride + x];
}

void clear(const image *image, color_t color) {
    size_t i;
    for (i = 0; i < image_pixel_count(image); i++) {
        image->buffer[i] = color;
    }
}

color_t rgb(uint32_t r, uint32_t g, uint32_t b) {
    const uint32_t alpha = 0xff;
    return alpha << 24 | (r & 0xff) << 16 | (g & 0xff) << 8 | (b & 0xff);
}

color_t rgbf(float r, float g, float b) {
    return rgb((uint32_t)(r * 255), (uint32_t)(g * 255), (uint32_t)(b * 255));
}

size_t get_alpha(color_t color) {
    return (color >> 24) & 0xff; 
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

size_t clamp(size_t x, size_t lo, size_t hi) {
    if (x < lo) return lo;
    if (x > hi) return hi;
    return x;
}

void draw_dens(const image *image, size_t N, float *dens) {
    assert(N <= image_width(image));
    assert(N <= image_height(image));
    const size_t size=(N+2)*(N+2);
    float hi = highf(dens, size);
    float lo = lowf(dens, size);
    for (size_t y = 0; y < N; y++) {
        for (size_t x = 0; x < N; x++) {
            float d = dens[x + y * (N+2) + 1];
            //uint32_t intensity = clamp((uint32_t)(255.0f * ((d - lo) / (hi - lo))), 0, 255);
            uint32_t intensity = (uint32_t)(128.0f * ((d - lo) / (hi - lo)));
            image->buffer[x + y * image->stride] = rgbf(intensity, intensity, intensity);
        }
    }
}

image create_image(size_t width, size_t height) {
    image image;
    image.buffer = malloc(sizeof(color_t) * width * height);
    image.resolution.width = width;
    image.resolution.height = height;
    image.stride = width;
    return image;
}
void destroy_image(const image *image) {
    free(image->buffer);
}

image load_rgba(const char* filename, size_t width, size_t height) {
    image image = create_image(width, height);
    FILE *fp;
    fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Could not open '%s': %s\n", filename, strerror(errno));
        exit(-1);
    }
    fread(image.buffer, sizeof(uint32_t), image_pixel_count(&image), fp);
    fclose(fp);
    return image;
}

color_t blend_color(color_t c1, color_t c2) {
    uint32_t c1_b = c1 & 0xff;
    uint32_t c1_g = (c1 >> 8) & 0xff;
    uint32_t c1_r = (c1 >> 16) & 0xff;

    uint32_t c2_b = c2 & 0xff;
    uint32_t c2_g = (c2 >> 8) & 0xff;
    uint32_t c2_r = (c2 >> 16) & 0xff;
    uint32_t a = (c2 >> 24) & 0xff;
    
    uint32_t ia = 0xff - a;
    //a = 0xff;
    //const ia = 0;
    return rgb(
        (c1_r * ia + c2_r * a) >> 8,
        (c1_g * ia + c2_g * a) >> 8,
        (c1_b * ia + c2_b * a) >> 8
    );
}

void blit(const image *target, const image *source, position_t position) {
    for (size_t sy = 0; sy < image_height(source); sy++) {
        const size_t ty = sy + position.y;
        for (size_t sx = 0; sx < image_width(source); sx++) {
            const size_t tx = sx + position.x;
            const color_t tc = target->buffer[tx + ty * target->stride];
            const color_t sc = source->buffer[sx + sy * source->stride];
            target->buffer[tx + ty * target->stride] = blend_color(tc, sc);
        }
    }
}

void image_scale(const image *target, const image *source) {
    for (size_t ty = 0; ty < image_height(target); ty++) {
        for (size_t tx = 0; tx < image_width(target); tx++) {
            const size_t sx = tx * image_width(source) / image_width(target);
            const size_t sy = ty * image_height(source) / image_height(target);
            const color_t color = source->buffer[sx + sy * source->stride];
            target->buffer[tx + ty * target->stride] = color;
        }
    }
}

position_t center(resolution_t outer, resolution_t inner) {
    position_t p;
    p.x = (outer.width - inner.width) / 2;
    p.y = (outer.height - inner.height) / 2;
    return p;
}

void dens_from_alpha(const image *image, float *dens, size_t N) {
    for (size_t y = 0; y < image_height(image); y++) {
        for (size_t x = 0; x < image_width(image); x++) {
            const color_t color = image_pixel(image, x, y);
            const size_t alpha = get_alpha(color);
            dens[y * (N+2) + x + 1] = alpha;
        }
    }
}

float randf() {
    return (float)rand() / RAND_MAX;
}

void flow(float *u, float *v, float uu, float vv, float ju, float jv, size_t N) {
    
    size_t y = N;
    for (size_t x = 1; x < N+1; x++) {
        u[(N+2) * y + x + 1] = uu + ju * (randf() - 0.5f);
        v[(N+2) * y + x + 1] = vv + jv * (randf() - 0.5f);
    }
}

int main() {
    const size_t N = 100;
    const size_t size=(N+2)*(N+2);
    float u[size], v[size], u_prev[size], v_prev[size];
    float dens[size], dens_prev[size];
    for (size_t i = 0; i < size; i++) {
        u[i] = v[i] = u_prev[i] = v_prev[i] = dens[i] = dens_prev[i] = 0.0f;
    }
    const float visc = 0.001, diff = 0.01;
    const float dt = 0.01;
    image screen = create_image(506, 253);
    const image im = load_rgba("hearth.bgra", 100, 100);
    
    dens_from_alpha(&im, dens, N);
    //flow(u_prev, v_prev, 5 / dt, 5.0f / dt, N);
    
    //image_scale
    const image dens_im = create_image(N, N);
    for (size_t frame = 0; frame < 1000; frame++) {
        flow(u, v, 0, -50.f, 5, 10, N);

        clear(&screen, 0xff222222);
        //get_from_UI ( dens_prev, u_prev, v_prev );
        vel_step(N, u, v, u_prev, v_prev, visc, dt);
        dens_step(N, dens, dens_prev, u, v, diff, dt);
        draw_dens(&dens_im, N, dens);
        image_scale(&screen, &dens_im);
        //blit(&screen, &im, center(screen.resolution, im.resolution));
        fwrite(screen.buffer, sizeof(uint32_t), image_pixel_count(&screen), stdout);
    }
    destroy_image(&dens_im);
    destroy_image(&im);
    destroy_image(&screen);
}