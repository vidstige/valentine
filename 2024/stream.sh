#!/bin/sh
RESOLUTION=${RESOLUTION:-720x720} 
ffplay -v warning -autoexit -f rawvideo -pixel_format rgb32 -framerate 30 -video_size $RESOLUTION -i -
