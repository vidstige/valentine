#!/bin/sh
RESOLUTION=${RESOLUTION:-720x720} 
ffmpeg -v warning -f rawvideo -pixel_format rgb32 -framerate 30 -video_size $RESOLUTION -i - $1
