#!/bin/bash
SIZE=100x100
convert "$1" -resize 100x80 -background transparent -gravity center -extent $SIZE "$2"
