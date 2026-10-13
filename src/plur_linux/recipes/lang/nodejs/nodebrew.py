import re
from plur import base_shell
from plur import base_node
NODE_VERSION='stable'

def setup_nodebrew(session):
    if not base_shell.check_command_exists(session, 'nodebrew'):
        if not base_shell.check_command_exists(session, 'perl'):
            platform = session.nodes[-1].platform
            if base_node.is_platform_rhel(platform):
                base_shell.yum_install(session, {'packages': ['perl']})
        base_shell.run(session, 'curl -L git.io/nodebrew | perl - setup')
        line = 'export PATH=$HOME/.nodebrew/current/bin:$PATH'
        base_shell.append_bashrc(session, line)

def nodebrew(session, *args):
    command = 'nodebrew ' + ' '.join(args)
    return base_shell.run(session, command)

def install_binary(session, version):
    nodebrew(session, 'list')
    nodebrew(session, 'clean', 'all')
    nodebrew(session, 'install-binary', version)
    nodebrew(session, 'use', version)
    nodebrew(session, 'list')

def uninstall_all_old(session):
    capture = nodebrew(session, 'list')
    lines = re.split('(\r\n|\n)', capture)
    current = ''
    for line in lines:
        if re.match('(current: )(.+|^[none])', line):
            current = re.split('current: ', line)[1].strip()
    for line in lines:
        if line.startswith(current):
            continue
        if re.match('(v|io@).+', line):
            nodebrew(session, 'uninstall', line)

def node_unstable_install(session, version='v0.11.15', harmony=True):
    options = ''
    if harmony:
        options = '--v8-options=--harmony'
    nodebrew(session, ['install', version, options])

def install(version):
    def func(session):
        setup_nodebrew(session)
        install_binary(session, version)
    return func

def input_node_params(self):
    from mini.menu import get_input
    if not hasattr(self, 'node_version'):
        self.node_version = NODE_VERSION
    self.node_version = get_input(expression=r'^(v\d{2}(\.\d{1,2})?|stable|latest)$', message='node ver[stable, v26, v26.3.1, etc.]' + f'({self.node_version}): ', default_value=self.node_version)
