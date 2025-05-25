from mini import misc
from plur import base_shell
from plur import session_wrap


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


def configure_docker(default_bridge_ip='10.192.192.254/26'):
    @session_wrap.sudo
    def func(session):
        docker_dir = '/etc/docker'
        if not base_shell.check_dir_exists(session, docker_dir):
            base_shell.run(session, 'mkdir -p ' + docker_dir)
            base_shell.run(session, 'chmod 700 ' + docker_dir)
        base_shell.here_doc(session, f'{docker_dir}/daemon.json', misc.del_indent_lines(f"""
        {{
          "bip": "{default_bridge_ip}"
        }}
        """))
        base_shell.run(session, 'systemctl restart docker')
    return func


def join_group(session):
    if session.nodes[-1].username != 'root':
        [base_shell.run(session, a) for a in misc.del_indent_lines("""
        sudo groupadd docker
        sudo usermod -aG docker $(whoami)
        """)]


def install(session):
    uninstall_old_versions(session)
    setup_the_repository(session)
    install_docker_engine(session)
    configure_docker()(session)
    join_group(session)

