for port in $(seq 7001 7006); 
do 
docker stop redis-cluster-${port}
done

