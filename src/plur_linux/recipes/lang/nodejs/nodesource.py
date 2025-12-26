from plur import base_shell
from plur import session_wrap


# setup from plur_linux.nodesource
def setup(version='18.x'):
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
        redhat(session)
            
    return func


