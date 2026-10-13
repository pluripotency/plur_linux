from plur.base_shell import run, work_on, yum_install


def prepare(session):
    packages = ['git', 'yum-utils', 'rpmdevtools', 'make']
    session.sudo_i()
    yum_install(session, packages)
    session.su_exit()
    clone = 'https://github.com/kazuhisya/nodejs-rpm.git'
    run(session, 'git clone %s' % clone)


def make_rpm(session):
    work_on(session, 'nodejs-rpm')
    run(session, 'sudo yum-builddep -y ./nodejs.spec')
    run(session, 'make rpm')


