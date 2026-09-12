#! /bin/bash
IMAGE_NAME=utftpd
CONTAINER_NAME=tftpserver
TFTP_DIR=/home/worker/tftpboot

CURRENT=$(cd $(dirname $0);pwd)
docker build -f ${CURRENT}/Dockerfile -t ${IMAGE_NAME} ${CURRENT}

if docker ps -a | grep -q ${CONTAINER_NAME}; then
  docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi

mkdir -p ${TFTP_DIR} && chmod 755 ${TFTP_DIR}

docker run \
    -d --restart always \
    -p 69:69/udp \
    --name=${CONTAINER_NAME} \
    -v ${TFTP_DIR}:/home/tftp_user/tftpboot:rw \
    ${IMAGE_NAME}
