kubectl apply -k .

kubectl exec -it redis redis-cli

# see config by kustomization.yaml
> config get maxmemory
> config get maxmemory-policy

kubectl delete -k .
