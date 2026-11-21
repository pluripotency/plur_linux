from mini import misc
from plur import base_shell
from plur import session_wrap
# https://docs.docker.com/engine/install/almalinux/
# https://docs.docker.com/engine/install/fedora/

def uninstall_old_versions(session):
    base_shell.run(session, misc.del_indent(r"""
    sudo dnf remove -y docker \
        docker-client \
        docker-client-latest \
        docker-common \
        docker-latest \
        docker-latest-logrotate \
        docker-logrotate \
        docker-engine \
        podman \
        runc
    """))

def setup_the_repository(session):
    platform = session.platform
    if platform.startswith('fedora'):
        base_shell.run(session, 'sudo dnf config-manager addrepo --from-repofile https://download.docker.com/linux/fedora/docker-ce.repo')
    else:
        base_shell.run(session, 'sudo dnf -y install dnf-plugins-core')
        base_shell.run(session, 'sudo dnf config-manager --add-repo https://download.docker.com/linux/alma/docker-ce.repo')

def configure_docker(default_bridge_ip='10.192.192.254/26', k8s=False):
    @session_wrap.sudo
    def func(session):
        daemon_json_lines = misc.del_indent_lines(f"""
        {{
          "bip": "{default_bridge_ip}"
        }}
        """)

        docker_dir = '/etc/docker/'
        if not base_shell.check_dir_exists(session, docker_dir):
            base_shell.run(session, 'mkdir -p ' + docker_dir)
            base_shell.run(session, 'chmod 700 ' + docker_dir)
        base_shell.here_doc(session, docker_dir + 'daemon.json', daemon_json_lines)
        if k8s:
            k8s_conf_lines = misc.del_indent_lines("""
            net.bridge.bridge-nf-call-ip6tables = 1
            net.bridge.bridge-nf-call-iptables = 1
            net.ipv4.ip_forward = 1
            """)
            base_shell.here_doc(session, '/etc/sysctl.d/k8s.conf', k8s_conf_lines)
        base_shell.run(session, 'sysctl --system')
    return func

def join_group(session):
    #
    if session.nodes[-1].username != 'root':
        actions = [
            'sudo groupadd docker',
            'sudo usermod -aG docker $(whoami)'
        ]
        [base_shell.run(session, action) for action in actions]

def install(session):
    uninstall_old_versions(session)
    setup_the_repository(session)
    base_shell.run(session, 'sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin')
    configure_docker()(session)
    base_shell.run(session, 'sudo systemctl enable --now docker')
    join_group(session)

