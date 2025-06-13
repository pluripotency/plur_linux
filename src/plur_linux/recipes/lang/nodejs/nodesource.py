from plur import base_shell
from plur import session_wrap


# setup from plur_linux.nodesource
def setup(version='18.x'):
    @session_wrap.sudo
    def for_centos7(session):
        base_shell.yum_install(session, {'packages': [
            # for npm build
            'make',
            'gcc-c++'
        ]})
        action = f'curl -fsSL https://rpm.nodesource.com/setup_{version} | bash -'
        base_shell.run(session, action)
        base_shell.yum_install(session, {'packages': [
            'nodejs',
        ]})

    @session_wrap.sudo
    def redhat(session):
        base_shell.run(session, 'dnf install -y ' + ' '.join([
            # for npm build
            'make',
            'gcc-c++'
        ]))
        action = f'curl -fsSL https://rpm.nodesource.com/setup_{version} | bash -'
        base_shell.run(session, action)
        base_shell.run(session, 'dnf install -y ' + ' '.join([
            'nodejs',
        ]))

    def func(session):
        platfrom = session.nodes[-1].platform
        if platfrom == 'centos7':
            for_centos7(session)
        else:
            redhat(session)
            
    return func


