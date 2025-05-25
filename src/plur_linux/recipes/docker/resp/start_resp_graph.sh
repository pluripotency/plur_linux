#! /bin/sh
IMAGE_NAME=resp_graph
CONTAINER_NAME=${IMAGE_NAME}
CURRENT=$(cd $(dirname $0);pwd)
if docker ps -a | grep -q ${CONTAINER_NAME}; then
  docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi

UPDATE_IMAGE_PATH=${CURRENT}/${IMAGE_NAME}.tar.gz
if [ -f ${UPDATE_IMAGE_PATH} ]; then
  docker load -i ${UPDATE_IMAGE_PATH}
  docker image prune -f
  rm -f ${UPDATE_IMAGE_PATH}
fi

REDIS_IP=127.0.0.1
CONFIG_PATH=/node/config/config.toml

docker run -d \
    --net host \
    --name ${CONTAINER_NAME} \
    --restart=always \
    -v ${CURRENT}/config:/node/config:ro \
    -e CONFIG_PATH=${CONFIG_PATH} \
    -e NODE_ENV=production \
    -e REDIS_IP=${REDIS_IP} \
    -e HOSTNAME=${HOSTNAME} \
    ${IMAGE_NAME} node js/server/app.js
