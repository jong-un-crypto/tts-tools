for port in $(seq 7001 7006); 
do 
docker rm redis-cluster-${port}
done

