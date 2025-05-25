#! /bin/sh
CONTAINER_NAME=nginx_jou
IMAGE_NAME=nginx

NET1=v0002
SUBNET1=172.25.0.0/22
IFACE1=eth1.2
IP1=172.25.3.180
IP1_GW=172.25.3.254

NET2=v0699
SUBNET2=192.168.113.0/24
IFACE2=eth1.699
IP2=192.168.113.201
IP2_GW=192.168.113.254

CURRENT=$(cd $(dirname $0);pwd)

docker network ls | egrep -q " ${NET1} +macvlan" || \
  docker network create -d macvlan --subnet=${SUBNET1} -o parent=${IFACE1} ${NET1}
docker network ls | egrep -q " ${NET2} +macvlan" || \
  docker network create -d macvlan --subnet=${SUBNET2} -o parent=${IFACE2} ${NET2}

if docker ps -a | grep -q ${CONTAINER_NAME}; then
  docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi

docker run -d --restart=always \
  --network=${NET1} \
  --ip=${IP1} \
  --name ${CONTAINER_NAME} \
  -v ${CURRENT}/assets/ted.conf:/etc/nginx/conf.d/default.conf \
  -v ${CURRENT}/assets/index.html:/pages/index.html \
  ${IMAGE_NAME}

CONT_ID=`docker ps -q -f name=^${CONTAINER_NAME}$`
CONT_NS=NS_${CONTAINER_NAME}
docker network connect --ip ${IP2} ${NET2} ${CONT_ID}

sudo ip netns add testing
sudo ip netns del testing
sudo ip netns del $CONT_NS
sudo ln -s /proc/`docker inspect ${CONT_ID} --format '{{.State.Pid}}'`/ns/net /var/run/netns/${CONT_NS}
sudo ip netns exec $CONT_NS ip r d default
sudo ip netns exec $CONT_NS ip r a default via ${IP2_GW}
sudo ip netns exec $CONT_NS ip r a 172.25.0.0/22 via ${IP1_GW}
sudo ip netns exec $CONT_NS ip r a 10.64.250.0/24 via ${IP1_GW}
sudo ip netns exec $CONT_NS ip r a 10.3.5.0/24 via ${IP1_GW}
sudo ip netns exec $CONT_NS ip r a 172.21.250.0/24 via ${IP1_GW}
sudo ip netns exec $CONT_NS ip r a 10.5.99.0/24 via ${IP1_GW}
sudo ip netns exec $CONT_NS ip r
sudo ip netns exec $CONT_NS ping ${IP2_GW} -c 2
sudo ip netns exec $CONT_NS ping ${IP1_GW} -c 2
sudo ip netns exec $CONT_NS ip -4 a
