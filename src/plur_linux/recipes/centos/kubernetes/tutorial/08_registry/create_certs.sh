#! /bin/sh
openssl req \
  -newkey rsa:4096 -nodes -sha256 -keyout certs/my.key \
  -x509 -days 3650 -out certs/my.crt

cp certs/my.crt /etc/docker/certs.d/minion:32767
