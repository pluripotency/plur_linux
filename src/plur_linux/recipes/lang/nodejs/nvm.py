import re
from plur import session_wrap
from plur import base_shell

def setup_nvm(session):
    base_shell.run(session, 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash')

def install_node(session, version):
    base_shell.run(session, f'nvm install {version}')

def install(version):
    def func(session):
        if not base_shell.check_command_exists(session, 'nvm'):
            setup_nvm(session)
            base_shell.run(session, '. ~/.bashrc')
        if not base_shell.check_command_exists(session, 'node'):
            install_node(session, version)
    return func

def input_node_params(self):
    from mini.menu import get_input
    self.node_version = get_input(expression=r'^v\d{2}(\.\d{1,2})?$', message='node ver[v24, v20.16, etc.]' + f'({self.node_version}): ', default_value=self.node_version)
    return {
        'version': self.node_version,
    }
