#!/bin/sh
RESOLUTION=${RESOLUTION:-720x720} 
FPS=30
ffmpeg -hide_banner -f rawvideo -pixel_format rgb32 -framerate $FPS -video_size $RESOLUTION -i - -metadata comment="vidstige" -b:v 8000k $1

