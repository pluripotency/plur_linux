import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as base_shell


def check_installed(session, command='/opt/rrdtool-1.4.8/bin/rrdtool'):
    return base_shell.check_command_exists(session, command)


def install(session, url):
    if not check_installed(session):
        src_file = 'rrdtool-1.4.8.tar.gz'
        src_dir = 'rrdtool-1.4.8/'
        src_url = url + src_file
        dl_dir = '$HOME/Downloads/'
        base_shell.work_on(session, dl_dir)
        base_shell.yum_install(session, {'packages': [
            'wget'
        ]})

        if not base_shell.check_file_exists(session, dl_dir + src_file):
            if not base_shell.wget(session, src_url):
                if not base_shell.wget(session, 'http://oss.oetiker.ch/rrdtool/pub/' + src_file):
                    print('Couldn\'t wget rrdtool source file')
                    return

        base_shell.run(session, 'tar xvzf ' + dl_dir + src_file)
        base_shell.work_on(session, dl_dir + src_dir)

        base_shell.yum_install(session, {'packages': [
            'gcc',
            'glib2-devel',
            'pango-devel',
            'libxml2-devel'
        ]})

        [base_shell.run(session, cmd) for cmd in [
            './configure',
            'make',
            'sudo make install',
        ]]

