#! /bin/sh
IFACE=${1}
IMAGE_NAME=plur3_sniff_iperf3
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

docker run -t -d \
  --restart=always \
  --memory=512m \
  --name ${CONTAINER_NAME} \
  --net host \
  ${IMAGE_NAME} \
  iperf3 -s -p 5001
