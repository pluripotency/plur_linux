
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell


def prepare(session):
    packages = ['git', 'yum-utils', 'rpmdevtools', 'make']
    session.sudo_i()
    shell.yum_install(session, packages)
    session.su_exit()
    clone = 'https://github.com/kazuhisya/nodejs-rpm.git'
    shell.run(session, 'git clone %s' % clone)


def make_rpm(session):
    shell.work_on(session, 'nodejs-rpm')
    shell.run('sudo yum-builddep -y ./nodejs.spec')
    shell.run('make rpm')


