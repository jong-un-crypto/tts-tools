#docker network rm redis-cluster
#docker network create redis-cluster

for port in $(seq 7001 7006); 
do 
mkdir -p /opt/redis/node-${port}/conf
mkdir -p /opt/redis/node-${port}/data
touch /opt/redis/node-${port}/conf/redis.conf
cat  << EOF > /opt/redis/node-${port}/conf/redis.conf
port ${port}
requirepass 1234
bind 0.0.0.0
protected-mode no
daemonize no
appendonly yes
cluster-enabled yes 
cluster-config-file nodes.conf
cluster-node-timeout 5000
cluster-announce-ip 127.0.0.1
cluster-announce-port ${port}
cluster-announce-bus-port 1${port}
EOF
done

