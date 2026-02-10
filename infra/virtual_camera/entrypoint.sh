#!/bin/sh

# Start RTSP Server in background
/rtsp-simple-server &

# Wait for server to start
sleep 2

# Loop video to RTSP
# -re : read input at native frame rate
# -stream_loop -1 : loop infinitely
# -i /video.mp4 : input file
# -c copy : direct copy (no transcode) for speed
# -f rtsp : output format
ffmpeg -re -stream_loop -1 -i /video.mp4 -c copy -f rtsp rtsp://localhost:8554/live
