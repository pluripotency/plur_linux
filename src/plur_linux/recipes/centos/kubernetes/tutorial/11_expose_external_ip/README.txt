kubectl apply -f load-balancer-example.yaml

# confirm them

kubectl get deployments hello-world
kubectl describe deployments hello-world

kubectl get replicasets
kubectl describe replicasets


# expose them (you can access: minion:LoadBalancer Port, External IP will be pending)
kubectl expose deployment hello-world --type=LoadBalancer --name=my-service
kubectl get services my-service
kubectl describe services my-service

# curl http://minion:<port>

# delete
kubectl delete servces my-service
kubectl delete deployment hello-world
