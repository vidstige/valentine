#include <errno.h>
#include <stdio.h>
#include <string.h>

#include "image_io.h"
#include "image.h"

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

