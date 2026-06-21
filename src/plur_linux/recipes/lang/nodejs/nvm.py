from plur import base_shell
NVM_VERSION='v0.40.4'
NODE_VERSION='v26'

def setup_nvm(session):
    base_shell.run(session, f'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh | bash')

def install_node(session, version):
    base_shell.run(session, f'nvm install {version}')

def install(version=NODE_VERSION):
    def func(session):
        if not base_shell.check_command_exists(session, 'nvm'):
            setup_nvm(session)
            base_shell.run(session, '. ~/.bashrc')
        if not base_shell.check_command_exists(session, 'node'):
            install_node(session, version)
    return func

def input_node_params(self):
    from mini.menu import get_input
    if not hasattr(self, 'node_version'):
        self.node_version = NODE_VERSION
    self.node_version = get_input(expression=r'^v\d{2}(\.\d{1,2})?$', message='node ver[v26, v26.3.1, etc.]' + f'({self.node_version}): ', default_value=self.node_version)
