#! /bin/sh
kubectl -n kubernetes-dashboard create token admin-user

kubectl proxy &
firefox http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/ &