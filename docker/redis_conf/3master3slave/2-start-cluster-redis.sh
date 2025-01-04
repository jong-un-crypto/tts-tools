for port in $(seq 7001 7006); \
do \
   docker run -it -d -p ${port}:${port} -p 1${port}:1${port} \
  --privileged=true -v /opt/redis/node-${port}/conf/redis.conf:/usr/local/etc/redis/redis.conf \
  --privileged=true -v /opt/redis/node-${port}/data:/data \
  --restart always --name redis-cluster-${port} --net host \
  redis redis-server /usr/local/etc/redis/redis.conf
done

