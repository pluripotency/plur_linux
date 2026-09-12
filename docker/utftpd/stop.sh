#! /bin/bash
CONTAINER_NAME=tftpserver

CURRENT=$(cd $(dirname $0);pwd)
if docker ps -a | grep -q ${CONTAINER_NAME}; then
  docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi
