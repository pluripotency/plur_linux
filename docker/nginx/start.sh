#! /bin/bash
IMAGE_NAME=nginx_sphw
docker build . -t ${IMAGE_NAME}
docker rm -f `docker ps -qa -f name=^${IMAGE_NAME}$`

docker run -d --restart=always \
  --net=host \
  --name  ${IMAGE_NAME}\
  -v $PWD/conf.d:/etc/nginx/conf.d:ro \
  -v /mnt/MC/books:/mnt/MC/books:ro \
  ${IMAGE_NAME}
