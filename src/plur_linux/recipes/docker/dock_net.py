
def create_macvlan_str(subnet, gateway, iface, netname):
    return f"docker network create -d macvlan --subnet={subnet} --gateway={gateway} -o parent={iface} {netname}"


def attach_net_str(container_name, netname, address=None):
    if address:
        return f'docker network connect --ip {address} {netname} `docker ps -q -f name={container_name}`'
    else:
        return f'docker network connect {netname} `docker ps -q -f name={container_name}`'


def create_postup_str_list(container_name, command_list):
    postup = f"""
    CONT_ID=`docker ps -q -f name={container_name}$`
    CONT_NS={container_name}
    sudo ip netns add testing
    sudo ip netns del testing
    sudo ip netns del $CONT_NS"""

    postup += """
    sudo ln -s /proc/`docker inspect ${CONT_ID} --format '{{.State.Pid}}'`/ns/net /var/run/netns/${CONT_NS}
    """
    postup_list = [line[4:] for line in postup.split('\n')[1:]]
    for command in command_list:
        postup_list.append(f"sudo ip netns exec $CONT_NS {command}")

    return postup_list

