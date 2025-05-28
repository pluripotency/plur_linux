import re
from plur import session_wrap
from plur import base_shell

def setup_nodebrew(session):
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

def uninstall_old(session):
    capture = nodebrew(session, 'list')
    lines = re.split('(\r\n|\n)', capture)
    current = ''
    for line in lines:
        if re.match('(current: )(.+|^[none])', line):
            current = re.split('current: ', line)[1]
    for line in lines:
        if re.match('.*' + current, line):
            if re.match('(v0|io@).+', line):
                nodebrew(session, 'uninstall', line)

def node_unstable_install(session, version='v0.11.15', harmony=True):
    options = ''
    if harmony:
        options = '--v8-options=--harmony'
    nodebrew(session, ['install', version, options])

def setup_nodejs(version):
    def func(session):
        if not base_shell.check_command_exists(session, 'node'):
            if not base_shell.check_command_exists(session, 'nodebrew'):
                setup_nodebrew(session)
            # uninstall_old(session)
            install_binary(session, version)
    return func

def install(version):
    def func(session):
        if not base_shell.check_command_exists(session, 'nodebrew'):
            if not base_shell.check_command_exists(session, 'perl'):
                base_shell.yum_install(session, {'packages': ['perl']})
            setup_nodebrew(session)
            install_binary(session, version)
    return func

def input_node_params(self):
    from mini.menu import get_input
    self.node_version = get_input(expression=r'^v\d{2}(\.\d{1,2})?$', message='node ver[v22, v20.16, etc.]' + f'({self.node_version}): ', default_value=self.node_version)
    return {
        'version': self.node_version,
    }
