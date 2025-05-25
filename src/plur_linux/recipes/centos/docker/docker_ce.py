from misc import misc
from plur import base_shell
from plur import session_wrap


# https://docs.docker.com/install/linux/docker-ce/centos/

def uninstall_old_versions(session):
    base_shell.run(session, """yum remove -y docker \
    docker-client \
    docker-client-latest \
    docker-common \
    docker-latest \
    docker-latest-logrotate \
    docker-logrotate \
    docker-selinux \
    docker-engine-selinux \
    docker-engine
    """)


def setup_the_repository(session):
    base_shell.yum_y_install([
        "yum-utils",
        "device-mapper-persistent-data",
        "lvm2",
    ])(session)
    base_shell.run(session, """yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
    """)


def configure_docker(default_bridge_ip='10.192.192.254/26', k8s=True):
    def func(session):
        daemon_json_lines = misc.del_indent_lines(f"""
        {{
          "bip": "{default_bridge_ip}",
          "storage-driver": "overlay2",
          "exec-opts": [
            "native.cgroupdriver=systemd"
          ]
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


def install(version=None):
    @session_wrap.sudo
    def func1(session):
        uninstall_old_versions(session)
        setup_the_repository(session)
        if version:
            # example version = 18.06.0.ce-3.el7
            # example version = 18.09.0-3.el7
            base_shell.yum_install(session, {'packages': ['docker-ce-' + version]})
        else:
            base_shell.yum_install(session, {'packages': [
                'docker-ce'
                , 'docker-ce-cli'
                , 'containerd.io'
                , 'docker-compose-plugin'
            ]})
        configure_docker()(session)
        base_shell.service_on(session, 'docker')

    def func2(session):
        func1(session)
        join_group(session)

    return func2
