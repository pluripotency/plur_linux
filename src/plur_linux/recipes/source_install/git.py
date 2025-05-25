from plur.base_shell import *
from plur import session_wrap


def pre_install(session):
    if check_command_exists(session, 'git'):
        run(session, 'sudo yum remove -y git')


@session_wrap.sudo
def install_dependency(session):
    packages = [
        'gcc-c++'
        , 'make'
        , 'autoconf'
        , 'curl-devel'
        , 'expat-devel'
        , 'gettext-devel'
        , 'openssl-devel'
        , 'perl-devel'
        , 'zlib-devel'
    ]
    run(session, f'yum install -y {" ".join(packages)}')
    run(session, 'yum remove -y git')


def curl_master_then_work_on(session):
    projects_dir = '$HOME/Projects'
    work_on(session, projects_dir)

    extract_dir_head = 'git-git'
    run(session, f'rm -rf {extract_dir_head}*')

    tarball_master_url = 'https://github.com/git/git/tarball/master'
    actions = [
        f'curl -L {tarball_master_url} | tar xz'
        , f'cd {extract_dir_head}\t'
    ]
    [run(session, a) for a in actions]


def make_install(session):
    actions = [
        'make configure'
        , './configure --prefix=/usr/local'
        , 'sudo make install'
    ]
    [run(session, a) for a in actions]


def install(session):
    pre_install(session)
    install_dependency(session)
    curl_master_then_work_on(session)
    make_install(session)


if __name__ == '__main__':
    from plur import base_node
    import getpass
    password = getpass.getpass('input password: ')

    hostname = 'localhost'
    access_ip = '10.0.2.4'
    node = base_node.Linux(hostname, password=password)
    node.access_ip = access_ip

    @session_wrap.ssh(node)
    def func(session):
        install(session)

    func()


