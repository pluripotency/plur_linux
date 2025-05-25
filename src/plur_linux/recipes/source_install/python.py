import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
import recipes.source_install.base as src_base


def prepare_packages(session):
    packages = [
        'zlib-devel'
        , 'ncurses-devel'
        , 'openssl-devel'
        , 'sqlite-devel'
        , 'readline-devel'
        , 'tk-devel'
        , 'gcc-c++'
        , 'automake'
        , 'autoconf'
        , 'libtoolize'
        , 'make'
    ]
    shell.yum_install(session, {'packages': packages})


def install(session, version):

    download_dir = '$HOME/Downloads/'
    package_dir = 'Python-%s' % version
    package_file = package_dir + '.tgz'
    src_url = 'https://python.org/ftp/python/%s/%s' % (version, package_file)
    shell.work_on(session, download_dir)
    if not shell.check_dir_exists(session, download_dir+package_dir):
        shell.wget(session, src_url)
        shell.run(session, 'tar xvzf ' + package_file)

    build_env = src_base.prepare_build_env(session, download_dir + package_dir)
    prepare_packages(session)

    # Configure and make
    conf_options = [
        '--prefix=/usr/local',
    ]
    src_base.configure(session, conf_options)
    src_base.make_and_altinstall(session)


def install_python2(session, version='2.7.11'):
    install(session, version)


def install_python3(session, version='3.6.2'):
    install(session, version)


