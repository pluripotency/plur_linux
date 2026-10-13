from plur import base_shell
from plur_linux.recipes import firewalld


def create_portainer(session):
    service_port = '9000'
    work_dir = '~/Projects/portainer'
    base_shell.work_on(session, work_dir)
    create_volume = 'docker volume create portainer_data'
    base_shell.run(session, create_volume)
    base_shell.here_doc(session, rf'{work_dir}/start_docker.sh', f"""
    #! /bin/bash
    
    {create_volume}
    
    docker run -d --name=portainer \
        -p 8000:8000 \
        -p {service_port}:9000 \
        --restart=always \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v portainer_data:/data \
        portainer/portainer
    """.split('\n    ')[1:])
    firewalld.configure(ports=[f'{service_port}/tcp'], add=True)(session)
    base_shell.run(session, 'sh start_docker.sh')


def create_cadvisor(session):
    service_port = '8080'
    work_dir = '~/Projects/cadvisor'
    base_shell.work_on(session, work_dir)
    base_shell.here_doc(session, rf'{work_dir}/start_docker.sh', f"""
    VERSION=v0.36.0 # use the latest release version from https://github.com/google/cadvisor/releases
    sudo docker run \
      --volume=/:/rootfs:ro \
      --volume=/var/run:/var/run:ro \
      --volume=/sys:/sys:ro \
      --volume=/var/lib/docker/:/var/lib/docker:ro \
      --volume=/dev/disk/:/dev/disk:ro \
      --publish={service_port}:8080 \
      --detach=true \
      --name=cadvisor \
      --privileged \
      --device=/dev/kmsg \
      gcr.io/google-containers/cadvisor:$VERSION
    """.split('\n    ')[1:])
    firewalld.configure(ports=[f'{service_port}/tcp'], add=True)(session)
    base_shell.run(session, 'sh start_docker.sh')


