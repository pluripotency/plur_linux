from mini import misc
from plur import base_shell
from plur_linux.recipes.docker import common
# https://docs.docker.com/engine/install/centos/
# For CentOS 9(Stream)

def uninstall_old_versions(session):
    base_shell.run(session, misc.del_indent("""
    sudo yum remove -y docker \
        docker-client \
        docker-client-latest \
        docker-common \
        docker-latest \
        docker-latest-logrotate \
        docker-logrotate \
        docker-engine
    """))


def setup_the_repository(session):
    [base_shell.run(session, a) for a in misc.del_indent_lines("""
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    """)]


def install_docker_engine(session):
    [base_shell.run(session, a) for a in misc.del_indent_lines("""
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker
    """)]


def install(session):
    if not base_shell.check_command_exists(session, 'docker'):
        uninstall_old_versions(session)
        setup_the_repository(session)
        install_docker_engine(session)
        common.configure_docker()(session)
        common.join_group(session)

