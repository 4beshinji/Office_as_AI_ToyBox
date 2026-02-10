FROM bluenviron/mediamtx:latest AS rtsp
FROM jrottenberg/ffmpeg:4.4-alpine

COPY --from=rtsp /mediamtx /mediamtx
COPY --from=rtsp /mediamtx.yml /mediamtx.yml

# Copy a sample video (You need to provide this or download it)
# For this scaffold, we'll assume a 'video.mp4' exists in context
# or we just use a test pattern source if file missing.
# If video.mp4 is missing, ffmpeg will fail. We should generate a test pattern instead.
# COPY video.mp4 /video.mp4

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
