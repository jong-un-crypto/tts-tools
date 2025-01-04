### docker 做 redis-cluster 3 主 3 从

wsl2 下 docker 终于支持 systemd
systemctl status docker

```sh sudo ./install-docker.sh
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh

if [ ! $(getent group docker) ];
then
    sudo groupadd docker;
else
    echo "docker user group already exists"
fi

sudo gpasswd -a $USER docker
sudo service docker restart

rm -rf get-docker.sh
```

```sh 安装docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.22.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

- init 初始化配置文件和数据

```sh
sh 1-config-cluster-redis.sh  生成redis conf
```

- docker-compose 替代 docker run 部署 redis

```yaml
version: "3.4"

x-image: &default-image redis:latest
x-restart: &default-restart always
x-netmode: &default-netmode host

services:
  redis1:
    image: *default-image
    container_name: redis-cluster-7001
    network_mode: *default-netmode
    restart: *default-restart
    volumes:
      - /opt/redis/node-7001/conf/data:/data
      - /opt/redis/node-7001/conf/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "7001:7001"
      - "17001:17001"
    environment:
      - REDIS_PORT=7001
      - CLUSTER_NAME=test

  redis2:
    image: *default-image
    container_name: redis-cluster-7002
    network_mode: *default-netmode
    restart: *default-restart
    volumes:
      - /opt/redis/node-7002/conf/data:/data
      - /opt/redis/node-7002/conf/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "7002:7002"
      - "17002:17002"
    environment:
      - REDIS_PORT=7002

  redis3:
    image: *default-image
    container_name: redis-cluster-7003
    network_mode: *default-netmode
    restart: *default-restart
    volumes:
      - /opt/redis/node-7003/conf/data:/data
      - /opt/redis/node-7003/conf/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "7003:7003"
      - "17003:17003"
    environment:
      - REDIS_PORT=7003

  redis4:
    image: *default-image
    container_name: redis-cluster-7004
    network_mode: *default-netmode
    restart: *default-restart
    volumes:
      - /opt/redis/node-7004/conf/data:/data
      - /opt/redis/node-7004/conf/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "7004:7004"
      - "17004:17004"
    environment:
      - REDIS_PORT=7004

  redis5:
    image: *default-image
    container_name: redis-cluster-7005
    network_mode: *default-netmode
    restart: *default-restart
    volumes:
      - /opt/redis/node-7005/conf/data:/data
      - /opt/redis/node-7005/conf/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "7005:7005"
      - "17005:17005"
    environment:
      - REDIS_PORT=7005

  redis6:
    image: *default-image
    container_name: redis-cluster-7006
    network_mode: *default-netmode
    restart: *default-restart
    volumes:
      - /opt/redis/node-7006/conf/data:/data
      - /opt/redis/node-7006/conf/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "7006:7006"
      - "17006:17006"
    environment:
      - REDIS_PORT=7006
```

- 启动 docker-compose

```sh
sudo docker-compose up -d
docker ps
docker stop $(docker ps -a -q)

docker inspect -f='{{.Name}} {{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}} {{.HostConfig.PortBindings}}' $(docker ps -aq)
```

- 部署 cluster

```sh
sh 3-set-cluster-redis.sh
```

- 进入容器

```
docker exec -it redis-cluster-7001 /bin/bash
```

- Q & A
  redis 事务+watch 命令实现乐观锁，redis cluster 不支持事务，不支持多键操作如 mset
  failover 自动故障转移
  6 台 redis, cluster 多副本冗余和分布式分片方案 slot 槽位 16384
