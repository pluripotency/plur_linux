#! /bin/sh
IFACE=${1}
IMAGE_NAME=plur3_sniff_sniffer
CONTAINER_NAME=plur3_sniff_sniffer
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
  --memory=512m \
  --name ${CONTAINER_NAME} \
  --net host \
  ${IMAGE_NAME} \
  /opt/venv/bin/python -u ./start.py $IFACE

# this is needed to wait for ready
sleep 1