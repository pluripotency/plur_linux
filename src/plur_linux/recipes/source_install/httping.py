import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
from recipes.source_install import base as src_base


def check_installed(session, command='httping'):
    return shell.check_command_exists(session, command)


def install(session, url):
    if url and not check_installed(session):
        shell.yum_install(session, {'packages': ['gcc', 'gettext']})

        src_dir = 'httping-2.3.4'
        src_file = 'httping-2.3.4.tgz'
        src_url = url + src_file

        src_base.prepare_work_dir(session, src_dir, src_file, src_url)
        shell.run(session, 'make && sudo make install')

