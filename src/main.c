#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "array2f.h"
#include "color.h"
#include "image.h"
#include "solver.h"

#ifndef M_PI
#    define M_PI 3.14159265358979323846
#endif

void convolution(const array2f *source, const array2f *kernel, const array2f *target) {
    assert(source->resolution.width == target->resolution.width);
    assert(source->resolution.height == target->resolution.height);
    assert(kernel->resolution.width % 2 == 1);
    assert(kernel->resolution.height % 2 == 1);
    const size_t half_x = kernel->resolution.width / 2;
    const size_t half_y = kernel->resolution.height / 2;
    for (size_t x = half_x; x < source->resolution.width - half_x; x++) {
        for (size_t y = half_y; y < source->resolution.height - half_y; y++) {
            float tmp = 0;
            for (size_t kx = 0; kx < kernel->resolution.width; kx++) {
                for (size_t ky = 0; ky < kernel->resolution.height; ky++) {
                    tmp += array2f_get(kernel, kx, ky) * array2f_get(source, x + kx - half_x, y + ky - half_y);
                }
            }
            array2f_set(target, x, y, tmp);
        }
    }
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

void draw_dens(const image *image, array2f dens) {
    assert(dens.resolution.width <= image_width(image));
    assert(dens.resolution.height <= image_height(image));
    //float hi = highf(dens, size), lo = lowf(dens, size);
    float hi = 1, lo = 0;
    for (size_t y = 0; y < dens.resolution.height; y++) {
        for (size_t x = 0; x < dens.resolution.width; x++) {
            float d = dens.buffer[x + y * dens.stride];
            //uint32_t intensity = clamp((uint32_t)(255.0f * ((d - lo) / (hi - lo))), 0, 255);
            uint32_t intensity = clamp((uint32_t)(255.0f * ((d - lo) / (hi - lo))), 0, 255);
            image->buffer[x + y * image->stride] = rgb(intensity, intensity, intensity);
        }
    }
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
    return (float)rand() / (float)RAND_MAX;
}

void flow(array2f a, size_t y, float mean, float amplitude) {
    for (size_t x = 0; x < a.resolution.width; x++) {
        a.buffer[a.stride * y + x] = mean + amplitude * (randf() - 0.5f);
    }
}

void array2f_fill(array2f a, float value) {
    size_t c = 0;
    for (size_t y = 0; y < a.resolution.height; y++) {
        for (size_t x = 0; x < a.resolution.width; x++) {
            a.buffer[c++] = value;
        }
        c += (a.stride - a.resolution.width);
    }
}

void array2f_rand(array2f a, float amplitude) {
    size_t c = 0;
    for (size_t y = 0; y < a.resolution.height; y++) {
        for (size_t x = 0; x < a.resolution.width; x++) {
            a.buffer[c++] = randf() * amplitude;
        }
        c += (a.stride - a.resolution.width);
    }
}
int main() {
    const size_t N = 100;
//    const size_t size=(N+2)*(N+2);

    array2f u = create_array2f(N + 2, N + 2); array2f_fill(u, 0.f);
    array2f v = create_array2f(N + 2, N + 2); array2f_fill(v, 0.f);
    array2f u_prev = create_array2f(N + 2, N + 2); array2f_fill(u_prev, 0.f);
    array2f v_prev = create_array2f(N + 2, N + 2); array2f_fill(v_prev, 0.f);
    
    array2f dens = create_array2f(N + 2, N + 2); array2f_fill(dens, 0.f);
    array2f dens_prev = create_array2f(N + 2, N + 2); array2f_fill(dens_prev, 0.f);

    const float visc = 0.001, diff = 0.0;
    const float dt = 0.01;
    image screen = create_image(506, 253);
    const image im = load_rgba("hearth.bgra", 100, 100);
    
    array2f_rand(array2f_pad(&dens, 2, 2), 1);
    //dens_from_alpha(&im, dens.buffer, N);
    
    //image_scale
    const image dens_im = create_image(N, N);
    for (size_t frame = 0; frame < 1000; frame++) {
        flow(u, N - 10, 0, 45);
        flow(v, N - 10, -5.0f, 5);

        clear(&screen, 0xff222222);
        //get_from_UI ( dens_prev, u_prev, v_prev );
        vel_step(N, u.buffer, v.buffer, u_prev.buffer, v_prev.buffer, visc, dt);
        dens_step(N, dens.buffer, dens_prev.buffer, u.buffer, v.buffer, diff, dt);
        draw_dens(&dens_im, array2f_pad(&dens, 1, 1));
        image_scale(&screen, &dens_im);
        //blit(&screen, &im, center(screen.resolution, im.resolution));
        fwrite(screen.buffer, sizeof(uint32_t), image_pixel_count(&screen), stdout);
    }
    destroy_image(&dens_im);
    destroy_image(&im);
    destroy_image(&screen);

    destroy_array2f(&u);
    destroy_array2f(&v);
    destroy_array2f(&u_prev);
    destroy_array2f(&v_prev);
    destroy_array2f(&dens);
    destroy_array2f(&dens_prev);
}