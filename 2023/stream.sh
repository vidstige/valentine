#!/bin/sh
RESOLUTION=${RESOLUTION:-720x720} 
ffplay -v warning -loop 0 -f rawvideo -pixel_format rgb24 -framerate 30 -video_size $RESOLUTION -i -
