#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>

#include "array2f.h"
#include "color.h"
#include "colormap.h"
#include "image.h"
#include "image_io.h"
#include "solver.h"
#include "xf.h"

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

void draw_array2f(const image *image, array2f dens, const colormap_t *colormap) {
    assert(dens.resolution.width <= image_width(image));
    assert(dens.resolution.height <= image_height(image));
    //float hi = highf(dens, size), lo = lowf(dens, size);
    float hi = 1, lo = 0;
    for (size_t y = 0; y < dens.resolution.height; y++) {
        for (size_t x = 0; x < dens.resolution.width; x++) {
            float d = dens.buffer[x + y * dens.stride];
            float intensity = clampf((d - lo) / (hi - lo), 0.f, 1.f);
            image->buffer[x + y * image->stride] = colormap_get(colormap, intensity);
        }
    }
}

void blit(const image *target, const image *source, position_t position) {
    for (size_t sy = 0; sy < image_height(source); sy++) {
        const size_t ty = sy + position.y;
        for (size_t sx = 0; sx < image_width(source); sx++) {
            const size_t tx = sx + position.x;
            target->buffer[tx + ty * target->stride] = source->buffer[sx + sy * source->stride];
        }
    }
}

position_t center(resolution_t outer, resolution_t inner) {
    position_t p;
    p.x = (outer.width - inner.width) / 2;
    p.y = (outer.height - inner.height) / 2;
    return p;
}

void alpha_to_array2f(const image *image, array2f *array) {
    for (size_t y = 0; y < image_height(image); y++) {
        for (size_t x = 0; x < image_width(image); x++) {
            const color_t color = image_pixel(image, x, y);
            array2f_set(array, x, y, get_alpha(color) / 255);
        }
    }
}

float randf() {
    return (float)rand() / (float)RAND_MAX;
}

void flow(array2f a, size_t y, float mean, float amplitude) {
    for (size_t x = 2; x < a.resolution.width - 2; x++) {
        a.buffer[a.stride * y + x] = mean + amplitude * (randf() - 0.5f);
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

void box_bounds(const bounds_t* bounds) {
    const size_t w = bounds->bx.resolution.width;
    const size_t h = bounds->bx.resolution.height;

	for (size_t j = 1; j < h - 1; j++) {
        array2f_set(&bounds->bx, 0, j, 1); // left edges points right
        array2f_set(&bounds->by, 0, j, 0);

        array2f_set(&bounds->bx, w - 1, j, -1); // right edge points left
        array2f_set(&bounds->by, w - 1, j, 0);
	}

	for (size_t i = 1; i < w - 1; i++) {
        array2f_set(&bounds->bx, i, 0, 0); // top edge points down
        array2f_set(&bounds->by, i, 0, 1);

        array2f_set(&bounds->bx, i, h - 1, 0); // bottom edge points up
        array2f_set(&bounds->by, i, h - 1, -1);
	}
}

void bounds_from_mask(bounds_t* bounds, const array2f *mask) {
    for (int j = 0; j < mask->resolution.height - 1; j++) {
        for (int i = 0; i < mask->resolution.width - 1; i++) {
            const float dx = array2f_get(mask, i + 1, j) - array2f_get(mask, i, j);
            const float dy = array2f_get(mask, i, j + 1) - array2f_get(mask, i, j);
            array2f_set(&(bounds->bx), i, j, dx);
            array2f_set(&(bounds->by), i, j, dy);
        }
    }
}

// Create a new image with the given resolution and centers the old one inside
void center_image(image* im, resolution_t resolution) {
    image tmp = create_image(resolution.width, resolution.height);
    blit(&tmp, im, center(resolution, im->resolution));
    // Destroy old image and overwrite with new
    destroy_image(im);
    *im = tmp;
}

void update_mask(array2f *energy, array2f *mask, float dt) {
    const resolution_t resolution = resolution_same(energy->resolution, mask->resolution);
    for (size_t y = 0; y < resolution.height; y++) {
        for (size_t x = 0; x < resolution.width; x++) {
            const float e = array2f_get(energy, x, y);
            const float m = array2f_get(mask, x, y);
            array2f_set(mask, x, y, fmaxf(m - e*0.0001, 0.f));
        }
    }
}

int main() {
    srand(1337);

    const resolution_t resolution = {506/3 + 2, 253/3 + 2};

    array2f u = create_array2f(resolution); array2f_fill(u, 0.f);
    array2f v = create_array2f(resolution); array2f_fill(v, 0.f);
    array2f u_prev = create_array2f(resolution); array2f_fill(u_prev, 0.f);
    array2f v_prev = create_array2f(resolution); array2f_fill(v_prev, 0.f);
    
    array2f dens = create_array2f(resolution); array2f_fill(dens, 0.f);
    array2f dens_prev = create_array2f(resolution); array2f_fill(dens_prev, 0.f);
    array2f energy = create_array2f(resolution); array2f_fill(energy, 0.f);

    const float visc = 0.001, diffusion = 0.0;
    const float dt = 0.01;
    image screen = create_image(506, 253);
    image im = load_rgba("heart2.bgra", 64, 64);
    
    //array2f_rand(array2f_pad(&dens, 2, 2), 1);

    // Create bounds
    bounds_t bounds;
    bounds.bx = create_array2f(resolution);
    bounds.by = create_array2f(resolution);
    array2f_fill(bounds.bx, 0.f);
    array2f_fill(bounds.by, 0.f);
    center_image(&im, resolution);
    array2f mask = create_array2f(resolution);
    alpha_to_array2f(&im, &mask);
    //box_bounds(&bounds);

    // black -> white
    //colormap_t colormap = create_colormap(2, rgb(0, 0, 0), rgb(0xff, 0xff, 0xff));
    // Argon
    colormap_t colormap = create_colormap(4,
        color_parse("#03001e"),
        color_parse("#7303c0"),
        color_parse("#ec38bc"),
        color_parse("#fdeff9"));
        
    //image_scale
    const image dens_im = create_image(resolution.width - 2, resolution.height - 2);
    for (size_t frame = 0; frame < 1000; frame++) {
        // Inject matter
        for (size_t x = 3; x < dens.resolution.width - 3; x++) {
            array2f_set(&dens, x, dens.resolution.height - 3, 0.5f);
        }
        
        // Create upwards swirly flow
        flow(u, resolution.height - 5, 0, 20);
        flow(v, resolution.height - 5, resolution.height * -0.03, 3);
     
        bounds_from_mask(&bounds, &mask);
        //array2f_norm2(&u, &v, &energy);
        //update_mask(&energy, &mask, dt);

        //get_from_UI ( dens_prev, u_prev, v_prev );
        velocity_step(&u, &v, &u_prev, &v_prev, &bounds, visc, dt);
        density_step(&dens, &dens_prev, &u, &v, &bounds, diffusion, dt);

        draw_array2f(&dens_im, array2f_pad(&dens, 1, 1), &colormap);
        
        //draw_array2f(&dens_im, array2f_pad(&energy, 1, 1), &colormap);
        //clear(&screen, 0xff222222);
        image_scale(&screen, &dens_im);
        //blit(&screen, &im, center(screen.resolution, im.resolution));
        fwrite(screen.buffer, sizeof(uint32_t), image_pixel_count(&screen), stdout);
    }
    destroy_image(&dens_im);
    destroy_colormap(&colormap);

    destroy_array2f(&bounds.bx);
    destroy_array2f(&bounds.by);
    destroy_array2f(&mask);

    destroy_image(&im);
    destroy_image(&screen);

    destroy_array2f(&energy);

    destroy_array2f(&u);
    destroy_array2f(&v);
    destroy_array2f(&u_prev);
    destroy_array2f(&v_prev);
    destroy_array2f(&dens);
    destroy_array2f(&dens_prev);
}
