#! /bin/sh
IMAGE_NAME=plur3_sniff_runner
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

GRAPH_IMAGE_NAME=resp_graph
GRAPH_IMAGE_PATH=${CURRENT}/${GRAPH_IMAGE_NAME}.tar.gz
if [ -f ${GRAPH_IMAGE_PATH} ]; then
  sh ${CURRENT}/start_${GRAPH_IMAGE_NAME}.sh
fi

KEY_HEAD=resp
ACCESS_HOSTNAME=${HOSTNAME}
ACCESS_IP=`hostname -I | awk '{print $1}'`
LOCAL_CONF_DIR=${CURRENT}/config
INNER_CONF_DIR=/home/plur/config
REDIS_IP=127.0.0.1

docker run \
  --rm \
  --name ${CONTAINER_NAME} \
  --net host \
  -e KEY_HEAD=${KEY_HEAD} \
  -e ACCESS_HOSTNAME=${ACCESS_HOSTNAME} \
  -e ACCESS_IP=${ACCESS_IP} \
  -e REDIS_IP=${REDIS_IP} \
  -e CONF_DIR=${INNER_CONF_DIR} \
  -v /tmp:/tmp:rw \
  -v ${LOCAL_CONF_DIR}:${INNER_CONF_DIR}:ro \
  -v $HOME/.ssh:/home/plur/.ssh:ro \
  --log-driver syslog \
  --log-opt syslog-address=udp://${HOSTNAME}:514 \
  --log-opt tag="resp" \
  --log-opt syslog-facility=local0 \
  ${IMAGE_NAME}
