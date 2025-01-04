## docker 搭建 redis-sentinel 架构 (1 主 2 从 3 哨兵)

**_安装 docker/docker-compose_**

- 配置文件 \*.conf 读写分离

```sh
mkdir -p /opt/redis/redis-master/data
mkdir -p /opt/redis/redis-master/logs

mkdir -p /opt/redis/redis-slave-1/data
mkdir -p /opt/redis/redis-slave-1/logs

mkdir -p /opt/redis/redis-slave-2/data
mkdir -p /opt/redis/redis-slave-2/logs
```

### docker run 方式启动

- 启动 redis-master 容器, 同时启动 redis-server

```sh
docker run -d -p 6379:6379 -p 26379:26379 --restart always -v ./redis-master.conf:/data/redis.conf -v ./sentinel-main.conf:/data/sentinel.conf --name redis-master redis:latest redis-server redis.conf

docker exec -it redis-master bash
```

- 启动 redis-slave-1 容器 同时启动 redis-server

```sh
docker run -d -p 6380:6380 -p 26380:26380 -v ./redis-slave-1.conf:/data/redis.conf -v ./sentinel-slave-1.conf:/data/sentinel.conf --name redis-slave-1 redis:latest redis-server redis.conf

docker exec -it redis-slave-1 /bin/bash

redis-cli -p 6380
127.0.0.1:7004> info replication
# Replication
role:slave
master_host:127.0.0.1
master_port:7003
master_link_status:down  # 表明从节点没有连接到主节点
```

- 启动 redis-slave-2 容器 同时启动 redis-server

```sh
docker run -d -p 6381:6381 -p 26381:26381 -v ./redis-slave-2.conf:/data/redis.conf -v ./sentinel-slave-2.conf:/data/sentinel.conf --name redis-slave-2 redis:latest redis-server redis.conf

docker exec -it redis-slave-2 /bin/bash
```

### docker-compose 方式启动

```sh
docker-compose up -d
docker ps
docker stop $(docker ps -a -q)
```

### 开启 redis sentinel

- 启动各个 docker 容器里哨兵

```sh
# 进入master 查看主从生效
docker exec -it redis-server-master redis-cli
127.0.0.1:6379> auth 123456
OK
127.0.0.1:6379> info replication
# Replication
role:master
connected_slaves:2
slave0:ip=172.18.0.3,port=6380,state=online,offset=4214,lag=1
slave1:ip=172.18.0.2,port=6381,state=online,offset=4214,lag=1

#分别进入到master和从节点 开启redis sentinel
##主哨兵
docker exec -it redis-server-master bash
redis-sentinel sentinel.conf

##两个从哨兵
docker exec -it redis-server-slave-1 bash
redis-sentinel [sentinel.conf] /usr/local/etc/redis/redis-sentinel.conf

docker exec -it redis-server-slave-2 bash
redis-sentinel [sentinel.conf] /usr/local/etc/redis/redis-sentinel.conf

Running in sentinel mode
```

- 查看(主)哨兵, 监测节点的健康状况

```sh
redis-cli -p 26379
```

- 测试选举

```sh
#关闭master, 查看从节点是否变为了主节点, slave-1上位
docker stop redis-server-master

# 恢复master 看看是否变为了从节点
docker start redis-server-master
127.0.0.1:6379> auth 123456
OK
127.0.0.1:6379> info replication
# Replication
role:slave

# sentinel 打印的选举日志
docker inspect redis-server-master | grep IPAddress

docker inspect -f='{{.Name}} {{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}} {{.HostConfig.PortBindings}}' $(docker ps -aq)

docker logs -f -t --tail 100 redis-server-master
```

- Q & A

* redis 启动和 sentinel 启动 都放在 docker-compose.yml 之中, 做不了
* sentinel 的启动必须要进入到容器里面，手动启动, 而且如果主节点挂掉之后重启，sentinel 也需要手动重启一遍
* 脚本化, 服务化, 开机自启动
* docker 没预安装 vim 等基础工具, 费劲
