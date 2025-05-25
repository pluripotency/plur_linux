#! /bin/sh
if [ $# -ne 2 ];then
  echo "Usage: $0 [IP of v0118] [http target]"
  exit 0
fi
HTTPING_SRC_IP=${1}
HTTPING_TARGET=${2}

CURRENT=$(cd $(dirname $0);pwd)

CONTAINER_NAME=hping_creg3
IMAGE_NAME=busybox

NET1=v0118
SUBNET1=172.27.118.0/28
IFACE1=eth1.118
#IP1=172.27.118.3
IP1=${HTTPING_SRC_IP}
IP1_GW=172.27.118.14

docker network ls | egrep -q " ${NET1} +macvlan" || \
  docker network create -d macvlan --subnet=${SUBNET1} --gateway=${IP1_GW} -o parent=${IFACE1} ${NET1}

if docker ps -a | grep -q ${CONTAINER_NAME}; then
  docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi

docker run -it -d \
  --network=${NET1} \
  --ip=${IP1} \
  --name ${CONTAINER_NAME} \
  ${IMAGE_NAME} sleep 10

CONT_ID=`docker ps -q -f name=^${CONTAINER_NAME}$`
CONT_NS=NS_${CONTAINER_NAME}

sudo ip netns add testing
sudo ip netns del testing
sudo ip netns del $CONT_NS
sudo ln -s /proc/`docker inspect ${CONT_ID} --format '{{.State.Pid}}'`/ns/net /var/run/netns/${CONT_NS}
sudo ip netns exec $CONT_NS ip r d default
sudo ip netns exec $CONT_NS ip r a default via ${IP1_GW}
#sudo ip netns exec $CONT_NS ip r
#sudo ip netns exec $CONT_NS ping ${IP1_GW} -c 2
#sudo ip netns exec $CONT_NS ip -4 a
#sudo ip netns exec $CONT_NS httping -S -c 3 https://certregister.intra.riken.jp/dummy
sudo ip netns exec $CONT_NS httping -S -c 3 ${HTTPING_TARGET}

if docker ps -a | grep -q ${CONTAINER_NAME}; then
  docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
fi
