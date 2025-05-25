# ! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
from plur import output_methods
from recipes.source_install import base as src_base

import re

send_line = output_methods.send_line
waitprompt = output_methods.waitprompt


def check_installed(session, command='redis-cli'):
    return shell.check_command_exists(session, command)


def install(version='2.8.19', test=False):
    """redis install from source
    """
    def func(session):
        if not check_installed(session):
            src_dir = 'redis-%s' % version
            src_file = src_dir + '.tar.gz'
            src_url = 'http://download.redis.io/releases/%s' % src_file

            # check if previous build environment exists
            build_env = src_base.check_build_env(session, src_dir)
            work_dir = build_env['work_dir']
            src_parent_dir = build_env['src_parent_dir']
            download_dir = build_env['download_dir']
            bin_dir = build_env['bin_dir']

            prepare_packages(session)

            if build_env['dir_not_exists']:
                # Download source and extract
                src_base.wget_and_extract(session, src_url, src_file, src_dir, download_dir=download_dir)

                # create working directory
                src_base.mk_src_dir(session, src_dir, src_parent_dir=src_parent_dir, extracted_dir=download_dir)

            shell.work_on(session, work_dir)

            # Run make test
            if test:
                if re.match('centos.?', session.platform):
                    shell.run(session, 'sudo yum install -y tcl')
                src_base.make(session, ['test'], stdout=True)

            # These steps are same between Ubuntu and CentOS
            # make binary
            src_base.make(session, stdout=True)

            session.sudo_i()
            # configure sysctl
            conf_sysctl(session)

            # make install, then utils/install_server.sh
            shell.work_on(session, work_dir)
            src_base.make(session, ['install'], stdout=True)
            session.do(utils_install_server_sh())

            session.su_exit()
            shell.run(session, 'cd')
    return func


def prepare_packages(session):
    packages = [
        'gcc-c++'
        , 'make'
        , 'wget'
    ]
    shell.run(session, 'sudo yum remove -y redis')
    shell.yum_install(session, {'packages': packages})


def conf_sysctl(session):
    # configure sysctl.conf
    sysctl_file = '/etc/sysctl.conf'
    shell.create_backup(session, sysctl_file)
    # add overcommit memory to sysctl.conf
    if not shell.count_by_egrep(session, '^vm\.overcommit_memory = 1$', sysctl_file):
        shell.run(session, 'echo "" >> %s' % sysctl_file)
        shell.run(session, 'echo "# added for redis" >> %s' % sysctl_file)
        shell.run(session, 'echo "vm.overcommit_memory = 1" >> %s' % sysctl_file)


def utils_install_server_sh():
    action = './utils/install_server.sh'
    sendlines = [
        ['Please select the redis port for this instance: [6379]', '6379']
        , ['Please select the redis config file name [/etc/redis/6379.conf]', '/etc/redis/redis.conf']
        , ['Please select the redis log file name [/var/log/redis_6379.log]', '/var/log/redis.log']
        , ['Please select the data directory for this instance [/var/lib/redis/6379]', '/var/lib/redis']
        , ['Please select the redis executable path [', '/usr/local/bin/redis-server']
        , ['Is this ok? Then press ENTER to go on or Ctrl-C to abort.', '']
    ]
    rows = []
    for line in sendlines:
        line[0] = line[0].replace('[', '\[').replace(']', '\]').replace('?', '\?').replace('.', '\.')
        rows += [[line[0], send_line, line[1], line[0]]]
    rows += [['', waitprompt, '', '']]

    return shell.create_sequence(action, rows)


