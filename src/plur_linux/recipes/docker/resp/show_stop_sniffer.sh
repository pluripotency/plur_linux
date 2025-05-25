#! /bin/sh
CONTAINER_NAME=plur3_sniff_sniffer
docker logs `docker ps -aq -f name=^${CONTAINER_NAME}$`
docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
