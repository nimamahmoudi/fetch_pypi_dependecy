```
kubectl apply -f build-deps-job.yml

kubectl get pod pypi-requirements

kubectl describe pod/pypi-requirements

kubectl logs pypi-requirements -c fetch-packages
kubectl logs pypi-requirements -c extract-dependencies
kubectl logs pypi-requirements -c parse-dependencies

kubectl logs pypi-requirements
```