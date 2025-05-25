#! /bin/bash
kubectl create secret generic --namespace wordpress-mysql mysql-pass --from-literal=password=mysqlpassword
kubectl get secrets
