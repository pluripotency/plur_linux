#! /bin/sh
# https://github.com/fauria/docker-vsftpd
CONTAINER_NAME=vsftpd
CURRENT=$(cd $(dirname $0);pwd)
if docker ps -a | grep -q ${CONTAINER_NAME}; then
    docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi
PASV_ADDRESS=127.0.0.1
FTP_USER=respuser
FTP_PASS=resppass
DATA_DIR=${CURRENT}/data
docker run -d -v ${DATA_DIR}:/home/vsftpd \
    --name ${CONTAINER_NAME} --restart=always \
    -p 20:20 -p 21:21 -p 21100-21110:21100-21110 \
    -e FTP_USER=${FTP_USER} -e FTP_PASS=${FTP_PASS} \
    -e PASV_ADDRESS=${PASV_ADDRESS} -e PASV_MIN_PORT=21100 -e PASV_MAX_PORT=21110 \
    -e REVERSE_LOOKUP_ENABLE=NO \
    fauria/vsftpd
