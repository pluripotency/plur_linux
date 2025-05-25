from plur import base_shell
from recipes.ubuntu import ops
from lib import misc


def uninstall_old(session):
    base_shell.run(session, 'sudo apt-get remove ' + ' '.join([
        'docker.io',
        'docker-compose',
        'docker-compose-v2',
        'docker-doc',
        'podman-docker',
        'containerd',
        'runc',
    ]))


def prepare_repository(session):
    ops.sudo_apt_get_install_y(misc.del_indent_lines("""
    ca-certificates
    curl
    """), update=True)(session)
    [base_shell.run(session, a) for a in [
        'sudo install -m 0755 -d /etc/apt/keyrings',
        'sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc',
        'sudo chmod a+r /etc/apt/keyrings/docker.asc',
    ]]
    base_shell.run(session, r"""echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
         $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
     """)


def install(session):
    # checked 2024/06/11 https://docs.docker.com/engine/install/ubuntu/
    # os requirements 24.04 22.04 20.04
    uninstall_old(session)
    prepare_repository(session)

    ops.sudo_apt_get_install_y(misc.del_indent_lines("""
    docker-ce
    docker-ce-cli
    containerd.io
    docker-buildx-plugin
    docker-compose-plugin
    """), update=True)(session)
    base_shell.run(session, 'reset')

    if session.nodes[-1].username != 'root':
        [base_shell.run(session, a) for a in [
            'sudo groupadd docker',
            'sudo usermod -aG docker $(whoami)'
        ]]
    base_shell.run(session, r"echo {\"bip\": \"10.192.192.254/26\"} | sudo tee /etc/docker/daemon.json > /dev/null")
    base_shell.run(session, "sudo systemctl restart docker")
