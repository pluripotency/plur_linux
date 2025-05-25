from plur import base_shell
from . import dock_util

image_name = 'git_repository'
instance_name = 'git_repos'
repo_password = 'password'
docker_file_contents = f"""
FROM ubuntu:16.04

RUN apt-get update && apt-get install -y openssh-server git
RUN mkdir /var/run/sshd
RUN echo 'root:{repo_password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
"""

start_sh_name = 'start.sh'
start_sh_contents = f"""
#! /bin/sh
docker run -d -p 29999:22 --name {instance_name} {image_name} 
"""

destroy_sh_name = 'destroy.sh'
destroy_sh_contents = f"""
#! /bin/sh
docker rm -f `docker ps -aq -f name={instance_name}` 
"""


def deploy(session):
    dock_util.work_on(image_name)(session)
    if not dock_util.is_running(session, instance_name):
        if not dock_util.is_built(session, image_name):
            base_shell.here_doc(session, 'Dockerfile', docker_file_contents.split('\n')[1:])
            base_shell.run(session, f'docker build . -t {image_name}')

        if not base_shell.check_file_exists(session, start_sh_name):
            base_shell.here_doc(session, start_sh_name, start_sh_contents.split('\n')[1:])
            base_shell.here_doc(session, destroy_sh_name, destroy_sh_contents.split('\n')[1:])

        base_shell.run(session, f'sh {start_sh_name}')
