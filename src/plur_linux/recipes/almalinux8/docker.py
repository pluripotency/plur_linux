from plur import base_shell
from plur import session_wrap
from recipes.centos.docker import docker_ce
from recipes.centos.docker import docker_compose
from recipes import firewalld


@session_wrap.sudo
def as_root(session):
    if not base_shell.check_command_exists(session, 'docker'):
        firewalld.install_if_not_exists(session)
        docker_ce.uninstall_old_versions(session)
        docker_ce.setup_the_repository(session)
        base_shell.run(session, 'dnf install -y docker-ce --nobest --allowerasing')
        docker_ce.configure_docker()(session)
        base_shell.run(session, 'systemctl enable docker --now')
        docker_compose.install()(session)
        return True


def as_user(session):
    docker_ce.join_group(session)


def install(session):
    if as_root(session):
        as_user(session)
