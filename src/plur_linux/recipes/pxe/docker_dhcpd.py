
from mini import misc
from plur import base_shell
from plur_linux.recipes import firewalld
IMAGE_NAME='alpine-dhcpd'
dhcpd_cmd = ["/usr/sbin/dhcpd", "-4", "-f", "-d", "--no-pid", "-cf", "/etc/dhcp/dhcpd.conf", "-lf", "/var/lib/dhcp/dhcpd.leases" ]

def create_cmd_as_dockerfile_cmd():
    return '[' + ', '.join([f'"{item}"' for item in dhcpd_cmd]) + ']'

def create_cmd_as_delayed_cmd_arg():
    return '/bin/sh -c "sleep 2 && ' + ' '.join(dhcpd_cmd) + '"'

def prepare_dockerfile(dhcpd_dir):
    content_lines = misc.del_indent_lines(f"""
    FROM alpine:3.12
    RUN apk add --no-cache dhcp
    RUN ["touch", "/var/lib/dhcp/dhcpd.leases"]
    CMD {create_cmd_as_dockerfile_cmd()}
    """)
    file_path = f'{dhcpd_dir}/Dockerfile'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def prepare_start_sh(dhcpd_dir):
    content_lines = misc.del_indent_lines(r"""
    #! /bin/bash
    CURRENT=$(cd $(dirname $0);pwd)
    IMAGE_NAME=alpine-dhcpd
    CONTAINER_NAME=dhcpd

    docker build -f ${CURRENT}/Dockerfile -t ${IMAGE_NAME} ${CURRENT}

    if docker ps -a | grep -q ${CONTAINER_NAME}; then
      docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
    fi
    
    docker run -d --restart always \
        --net host \
        --name=$CONTAINER_NAME \
        -v $CURRENT/conf.d/dhcpd.conf:/etc/dhcp/dhcpd.conf:ro \
        -v $CURRENT/leases/:/var/lib/dhcpd:rw \
        $IMAGE_NAME
    
    """)
    file_path = f'{dhcpd_dir}/start.sh'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def prepare_stop_sh(dhcpd_dir):
    content_lines = misc.del_indent_lines("""
    #! /bin/sh
    CONTAINER_NAME=dhcpd
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
      docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
    fi
    """)
    file_path = f'{dhcpd_dir}/stop.sh'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def create_dhcpd_conf(dhcpd_dir, pxe_ip):
    from plur_linux.recipes.pxe import dhcpd_conf
    subnet_params = dhcpd_conf.get_subnet_params(pxe_ip)
    contents = dhcpd_conf.create_pxe_dhcp_conf_str(pxe_ip, subnet_params)
    file_path = f'{dhcpd_dir}/conf.d/dhcpd.conf'
    return lambda session: base_shell.here_doc(session, file_path, contents.split('\n'))

def start(pxe_ip, set_fw=False):
    dhcpd_dir = '~/Downloads/dhcpd'
    def func(session):
        if set_fw:
            firewalld.configure(services=['dhcp'], add=True)
        base_shell.work_on(session, f'{dhcpd_dir}/conf.d')
        base_shell.run(session, 'cd ..')
        prepare_dockerfile(dhcpd_dir)(session)
        prepare_start_sh(dhcpd_dir)(session)
        create_dhcpd_conf(dhcpd_dir, pxe_ip)(session)
        prepare_stop_sh(dhcpd_dir)(session)
        base_shell.run(session, 'chmod +x *.sh')
        base_shell.run(session, './start.sh')
    return func
