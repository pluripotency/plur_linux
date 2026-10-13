from mini import misc
from plur import base_shell
from plur_linux.recipes import firewalld
tftpboot_dir='/var/lib/tftpboot'

def prepare_dockerfile(tftpd_dir):
    content_lines = misc.del_indent_lines("""
    FROM ubuntu:22.04

    RUN apt-get update && apt-get install -y tftpd-hpa tftp-hpa && apt-get clean && rm -rf /var/lib/apt/lists/*
    ARG USERNAME=tftp_user
    ARG UID=1000
    RUN groupadd -g $UID $USERNAME && useradd -u $UID -g $UID -m $USERNAME
    USER $USERNAME
    WORKDIR /home/$USERNAME
    RUN mkdir tftpboot
    USER root
    CMD ["/usr/sbin/in.tftpd","--foreground","--user","tftp_user","--create","--address","0.0.0.0:69","--secure","/home/tftp_user/tftpboot"]
    """)
    file_path = f'{tftpd_dir}/Dockerfile'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def prepare_start_sh(tftpd_dir):
    content_lines = misc.del_indent_lines(rf"""
    #! /bin/bash
    IMAGE_NAME=utftpd
    CONTAINER_NAME=utftpd
    TFTP_DIR={tftpboot_dir}

    """)
    content_lines += misc.del_indent_lines(r"""
    CURRENT=$(cd $(dirname $0);pwd)
    docker build -f ${CURRENT}/Dockerfile -t ${IMAGE_NAME} ${CURRENT}

    if docker ps -a | grep -q ${CONTAINER_NAME}; then
      docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
    fi

    sudo chown -R ${TFTP_DIR} && sudo chmod 644 ${TFTP_DIR}

    docker run \
        -d --restart always \
        --net host \
        --name=${CONTAINER_NAME} \
        -v ${TFTP_DIR}:/home/tftp_user/tftpboot:ro \
        ${IMAGE_NAME}
    """)
    file_path = f'{tftpd_dir}/start.sh'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def prepare_stop_sh(tftpd_dir):
    content_lines = misc.del_indent_lines("""
    #! /bin/sh
    CONTAINER_NAME=utftpd
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
      docker rm -f `docker ps -aq -f name=^${CONTAINER_NAME}$`
    fi
    """)
    file_path = f'{tftpd_dir}/stop.sh'
    return lambda session: base_shell.here_doc(session, file_path, content_lines)

def start(set_fw=False):
    tftpd_dir = '~/Downloads/utftpd'
    def func(session):
        if set_fw:
            firewalld.configure(services=['tftp'], add=True)
        base_shell.work_on(session, tftpd_dir)
        prepare_dockerfile(tftpd_dir)(session)
        prepare_start_sh(tftpd_dir)(session)
        prepare_stop_sh(tftpd_dir)(session)
        base_shell.run(session, 'chmod +x *.sh')
        base_shell.run(session, './start.sh')
    return func

