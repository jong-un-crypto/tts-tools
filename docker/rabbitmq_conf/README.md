- docker 搭建 RabbitMQ

1. docker run 方式(不推荐)

```sh
  docker pull rabbitmq:management
  docker run -p 15672:15672 -p 5672:5672 -d --hostname dnmp-rabbitmq --name dnmp-rabbitmq -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=admin rabbitmq:management
```

2. docker-compose 方式(推荐)

```sh
docker-compose up -d
docker-compose stop
docker-compose restart

docker ps
docker stop $(docker ps -a -q)

docker inspect -f='{{.Name}} {{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}} {{.HostConfig.PortBindings}}' $(docker ps -aq)

```

3 进入容器

```sh
docker exec -it dnmp-rabbitmq /bin/bash

rabbitmq-plugins enable rabbitmq_management
```

4. Web 访问

```sh
http://localhost:15672
账号:admin
密码:123456

5672：用于 amqp 协议通信，用于程序连接 rabbitmq 使用。
15672：用于 rabbitmq 的 web 管控台访问端口。
```

5. <TODO> rabbitmq cluster
