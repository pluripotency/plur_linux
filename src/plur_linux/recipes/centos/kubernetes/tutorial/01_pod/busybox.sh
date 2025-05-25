#! /bin/sh
echo "nginx ip is $(kubectl get pod nginx -o go-template='{{.status.podIP}}')"
kubectl run busybox --image=busybox --restart=Never --tty -i --generator=run-pod/v1 --env "POD_IP=$(kubectl get pod nginx -o go-template='{{.status.podIP}}')"
kubectl delete pod busybox

