#! /bin/sh

# ~/.docker/config.json is created after login to registry
# docker login registry

cat ~/.docker/config.json | base64


# modify regcred.yml then create
# kubectl create -f regcred.yml
