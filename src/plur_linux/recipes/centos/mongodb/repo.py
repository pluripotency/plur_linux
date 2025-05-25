
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell

import re

all_packages = [
    'mongodb-org'
    , 'mongodb-org-server'
    , 'mongodb-org-shell'
    , 'mongodb-org-mongos'
    , 'mongodb-org-tools'
]

mongo2_centos_repo = [
    "[mongodb-2.6]",
    "name=MongoDB 2.6 Repository",
    "baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64/",
    "gpgcheck=0",
    "enabled=1"
]

mongo3_centos_repo = [
    "[mongodb-org-3.0]",
    "name=MongoDB Repository",
    r"baseurl=http://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.0/x86_64/",
    "gpgcheck=0",
    "enabled=1"
]


def prepare_repo(session, version):
    node = session.nodes[-1]
    if re.match('centos.?', session.platform):
        file_path = '/etc/yum.repos.d/mongodb.repos'
        repo = mongo2_centos_repo
        if version:
            if version.startswith('3'):
                repo = mongo3_centos_repo

        if repo:
            shell.here_doc(session, file_path, repo)

    elif node.platform == 'ubuntu':
        shell.run(session, 'apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10')
        source_list = ' '.join([
            'echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse"'
            , '|'
            , 'tee /etc/apt/sources.list.d/mongodb-org-3.0.list'
        ])
        shell.run(session, source_list)


def pin_version(session):
    if re.match('centos.?', session.platform):
        exclude = 'exclude=' + ','.join(all_packages)
        yum_conf = '/etc/yum.conf'
        if not shell.count_by_egrep(session, exclude, yum_conf):
            shell.run('echo %s >> %s' % (exclude, yum_conf))
    elif session.platform == 'ubuntu':
        [shell.run(session, 'echo "%s hold" | dpkg --set-selections' % pkg) for pkg in all_packages]


def package_install(session, version=None, cli_only=False):
    packages = all_packages
    if cli_only:
        packages = [all_packages[2]]

    if version:
        if re.match('centos.?', session.platform):
            pkgs = map(lambda x: x + '-' + version, packages)
            shell.yum_install(session, {'packages': pkgs})
        pin_version(session)
    else:
        shell.yum_install(session, {'packages': [packages[0]]})


def set_mongo_conf(session, replaces, appends):
    file_path = '/etc/mongod.conf'
    shell.create_backup(session, file_path)
    shell.sed_pipe(session, file_path + '.org', file_path, replaces)
    for append in appends:
        shell.run(session, 'echo "%s" >> %s' % (append, file_path))
    shell.run(session, 'service mongod restart')


def set_iptables(session, sentence, insert_before):
    if re.match('centos.?', session.platform):
        file_path = '/etc/sysconfig/iptables'
        shell.create_backup(session, file_path)

        all_in = True
        for al in sentence:
            check_expression = '^' + al + '$'
            if not shell.count_by_egrep(session, check_expression, file_path):
                all_in = False

        if all_in is False:
            expression = '^' + insert_before + '$'
            replace = '\\n'.join(sentence) + '\\n' + insert_before
            shell.sed_replace(session, expression, replace, file_path + '.org', file_path)

        shell.run(session, 'service iptables restart')


def enable_remote(session):
    if re.match('centos.?', session.platform):
        replaces = [
            ['^bind_ip=127.0.0.1$', '#bind_ip=127.0.0.1'],
            ['^#httpinterface=true$', 'httpinterface=true']
        ]
        appends = ['rest=true']
        set_mongo_conf(session, replaces, appends)

        sentence = [
            '-A INPUT -m state --state NEW -m tcp -p tcp --dport 27017 -j ACCEPT'
            , '-A INPUT -m state --state NEW -m tcp -p tcp --dport 28017 -j ACCEPT'
        ]
        insert_before = '-A INPUT -j REJECT --reject-with icmp-host-prohibited'
        set_iptables(session, sentence, insert_before)


def install(session, version=None, cli_only=False, remote_ok=True):
    # Check mongo is installed at first.
    if not shell.check_command_exists(session, 'mongo'):
        sudo_i = False
        if session.username != 'root':
            session.sudo_i()
            sudo_i = True

        prepare_repo(session, version)
        package_install(session, version, cli_only)

        if remote_ok:
            enable_remote(session)

        shell.service_on(session, 'mongod')

        if sudo_i:
            session.su_exit()


