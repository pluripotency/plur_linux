#! /bin/sh
POD_NAME=$(kubectl get pods nginx -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
kubectl label pod $POD_NAME app=test-nginx
