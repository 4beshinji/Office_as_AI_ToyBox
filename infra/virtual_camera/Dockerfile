FROM aler9/rtsp-simple-server AS rtsp
FROM jrottenberg/ffmpeg:4.4-alpine

COPY --from=rtsp /rtsp-simple-server /
COPY --from=rtsp /rtsp-simple-server.yml /

# Copy a sample video (You need to provide this or download it)
# For this scaffold, we'll assume a 'video.mp4' exists in context
# or we just use a test pattern source if file missing.
COPY video.mp4 /video.mp4

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
