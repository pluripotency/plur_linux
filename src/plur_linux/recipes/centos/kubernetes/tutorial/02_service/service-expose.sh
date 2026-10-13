#! /bin/sh
# not selector, its pod name
kubectl expose pod/nginx --port 80 --type="NodePort"
