# syntax=docker/dockerfile:experimental
FROM linuxserver/lidarr:latest

LABEL maintainer="Croneter"

RUN apt-get update \
    && apt-get -y --no-install-recommends install ffmpeg gawk \
    # Cleanup cache
    && apt-get clean autoclean \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/ /var/tmp/* /tmp/*

# Copy shell script that can be called
COPY --chown=root:users flac2mp3.sh /usr/local/bin/flac2mp3.sh
RUN chmod +x /usr/local/bin/flac2mp3.sh
