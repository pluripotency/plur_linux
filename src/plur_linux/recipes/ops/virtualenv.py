#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
virtualenv_dir = '$HOME/.virtualenv/'


def check_installed(session):
    if not shell.check_command_exists(session, 'virtualenv --version'):
        shell.yum_install(session, {'packages': ['python-setuptools']})
        shell.run(session, 'sudo easy_install virtualenv')


def add_virtualenv_to_bashrc(envname):
    def func(session):
        bashrc = '$HOME/.bashrc'
        alias = "alias %s='. %s%s/bin/activate'" % (envname, virtualenv_dir, envname)
        shell.run(session, 'sed -e "/^%s$/d" %s > %s' % (alias, bashrc, bashrc))
        shell.run(session, 'echo "%s" >> %s' % (alias, bashrc))
        # shell.run(session, '. %s' % bashrc)
    return func


def create_virtualenv(envname, python_path='`which python`'):
    def func(session):
        check_installed(session)
        shell.run(session, 'mkdir -p ' + virtualenv_dir)
        shell.work_on(session, virtualenv_dir)
        shell.run(session, 'virtualenv -p %s %s' % (python_path, envname))
        add_virtualenv_to_bashrc(envname)(session)

    return func


def activate(envname):
    def on(func):
        def _session(session):
            import copy
            envnode = copy.deepcopy(session.nodes[-1])
            envnode.waitprompt = '\(' + envname + '\) \[' + envnode.username + '@' + envnode.hostname + '.+\][#$] '
            session.push_node(envnode)

            shell.run(session, '. %s/bin/activate' % (virtualenv_dir + envname))
            result = func(session)

            session.pop_node()
            shell.run(session, 'deactivate')

            return result
        return _session
    return on
