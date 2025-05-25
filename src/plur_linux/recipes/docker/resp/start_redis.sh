#! /bin/sh

docker run -d \
    --name redis \
    -p 6379:6379 \
    --restart=always \
    -e TZ='Asia/Tokyo' \
    redis
