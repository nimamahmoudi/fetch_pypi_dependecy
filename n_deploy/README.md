```
kubectl apply -f build-deps-job.yml

kubectl get pod pypi-requirements2

kubectl describe pod/pypi-requirements2

kubectl logs pypi-requirements2 -c fetch-packages

kubectl logs pypi-requirements2


# Results:
kubectl port-forward pypi-requirements2 80

http://localhost/new_reqs.csv


# Delete:
kubectl delete pod pypi-requirements2

```