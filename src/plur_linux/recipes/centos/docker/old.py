from plur import base_shell
from plur import session_wrap


def create_repo(session):
    file_path = '~/docker.repos'
    contents = [
        "[dockerrepo]",
        "name=Docker Repository",
        "baseurl=https://yum.dockerproject.org/repo/main/centos/7/",
        "enabled=1",
        "gpgcheck=1",
        "gpgkey=https://yum.dockerproject.org/gpg"
    ]
    base_shell.here_doc(session, file_path, contents)
    base_shell.run(session, 'sudo mv %s /etc/yum.repos.d/' % file_path)


def join_group(session):
    if session.nodes[-1].username != 'root':
        actions = [
            'sudo groupadd docker',
            'sudo usermod -aG docker $(whoami)'
        ]
        [base_shell.run(session, action) for action in actions]
    else:
        actions = [
            'groupadd docker',
            'usermod -aG docker worker'
        ]
        [base_shell.run(session, action) for action in actions]


def check_exists(session, dev):
    # This is alternative of check_cmd_not_found
    test = 'if [ -e %s ];' % dev
    result = session.do(base_shell.check(test))
    session.child.expect(session.waitprompt)
    return result


@session_wrap.sudo
def setup_overlay2(session):
    daemon_json = """{
  "storage-driver": "overlay2",
  "exec-opts": [
    "native.cgroupdriver=systemd"
  ]
}
"""
    docker_dir = '/etc/docker/'
    if not base_shell.check_dir_exists(session, docker_dir):
        base_shell.run(session, 'mkdir -p /etc/docker/')
        base_shell.run(session, 'chmod 700 /etc/docker')
    base_shell.here_doc(session, '/etc/docker/daemon.json', daemon_json.split('\n'))


def setup_devicemapper(dev='/dev/vdb'):
    devicemapper_daemon_json = """{
  "storage-driver": "devicemapper",
  "storage-opts": [
    "dm.directlvm_device=%s",
    "dm.thinp_percent=95",
    "dm.thinp_metapercent=1",
    "dm.thinp_autoextend_threshold=80",
    "dm.thinp_autoextend_percent=20",
    "dm.directlvm_device_force=false"
  ],
  "exec-opts": [
    "native.cgroupdriver=systemd"
  ]
}
""" % dev

    @session_wrap.sudo
    def func(session):
        if check_exists(session, dev):
            base_shell.here_doc(session, '/etc/docker/daemon.json', devicemapper_daemon_json.split('\n'))
    return func


def install(session):
    create_repo(session)
    base_shell.yum_install(session, {'packages': ['docker-engine']})
    setup_overlay2(session)
    base_shell.service_on(session, 'docker')
    join_group(session)
    # setup_devicemapper('/dev/vdb')(session)


def uninstall(session):
    packages = [
        'docker',
        'docker-common',
        'container-selinux',
        'docker-selinux',
        'docker-engine'
    ]
    [base_shell.run(session, a) for a in [
        'sudo yum remove -y %s' % ' '.join(packages)
    ]]


def add_repo_docker_ce(session):
    if not base_shell.check_command_exists(session, 'yum-config-manager'):
        base_shell.yum_install(session, {'packages': ['yum-utils']})
    repo = 'https://download.docker.com/linux/centos/docker-ce.repo'
    [base_shell.run(session, a) for a in [
        'sudo yum-config-manager IPv4 --add-repos %s' % repo
    ]]


def on_enabled_repo_docker_ce(command, ce='docker-ce-stable'):
    # can be edge
    # ce = 'docker-ce-edge'
    return lambda session: [base_shell.run(session, a) for a in [
        'sudo yum-config-manager --enable %s' % ce,
        'sudo yum makecache IPv4 fast -y',
        command,
        'sudo yum-config-manager --disable %s' % ce,
    ]]


def uninstall_old_versions(session):
    base_shell.run(session, """sudo yum remove -y docker \
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
    base_shell.run(session, """sudo yum install -y yum-utils \
    device-mapper-persistent-data \
    lvm2
    """)
    base_shell.run(session, """sudo yum-config-manager \
    --add-repos \
    https://download.docker.com/linux/centos/docker-ce.repo
    """)


def install_docker_ce(session):
    add_repo_docker_ce(session)
    on_enabled_repo_docker_ce('sudo yum install -y docker-ce')(session)
    setup_overlay2(session)
    base_shell.service_on(session, 'docker')
    join_group(session)
    # setup_devicemapper('/dev/vdb')(session)


def update_docker_ce(session):
    on_enabled_repo_docker_ce('sudo yum update -y docker-ce')(session)


def upgrade_docker_ce(session):
    on_enabled_repo_docker_ce('sudo yum upgrade -y docker-ce')(session)


def uninstall_docker_ce(session):
    [base_shell.run(session, a) for a in [
        'sudo yum remove -y docker-ce',
        # 'sudo rm -rf /var/lib/docker'
    ]]
