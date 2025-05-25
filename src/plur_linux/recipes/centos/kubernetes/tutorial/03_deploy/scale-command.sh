#! /bin/sh
kubectl scale deploy nginx-deployment --replicas=4
kubectl get pod -o wide
