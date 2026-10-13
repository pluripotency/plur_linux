import os
from plur import base_shell
from plur import session_wrap
from plur_linux.recipes.ops import ops
from plur_linux.recipes.centos import chrony
from plur_linux.recipes import firewalld


@session_wrap.sudo
def enable_rest_api(session):
    service_port = '2376'
    override_file_path = '/etc/systemd/system/docker.service.d/override.conf'
    base_shell.create_dir(session, f'mkdir ' + os.path.dirname(override_file_path))
    base_shell.here_doc(session, override_file_path, f"""
    [Service]
    ExecStart=
    ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:{service_port}
    """.split('\n    ')[1:])
    base_shell.run(session, 'systemctl daemon-reload')
    base_shell.run(session, 'systemctl restart docker.service')
    firewalld.configure(ports=[f'{service_port}/tcp'], add=True)(session)


def install_docker_ce(session):
    ops.disable_selinux(session)
    base_shell.yum_install(session, {
        'packages': [
            'ebtables',
            'ethtool',
            'firewalld',
        ]
    })
    firewalld.configure(add=True)(session)
    chrony.configure(session)

    from plur_linux.recipes.centos.docker import docker_ce
    docker_ce.install(version=None)(session)

    from plur_linux.recipes.centos.docker import utils
    utils.create_script_to_count_restart(session)


def install_docker_if_not_installed(session):
    if not base_shell.check_command_exists(session, 'docker'):
        install_docker_ce(session)


