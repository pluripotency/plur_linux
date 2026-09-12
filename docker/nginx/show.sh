#! /bin/bash
IMAGE_NAME=nginx_sphw
docker logs -f `docker ps -qa -f name=^${IMAGE_NAME}$`
