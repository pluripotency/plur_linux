import os
import sys
sys.path.append(os.pardir)

from plur import base_shell


def install(session, version='v4.4.2'):
    src_dir = 'node-%s-linux-x64' % version
    session.sudo_i()

    work_dir = '~/'
    src_file = src_dir + '.tar.gz'
    url = 'https://nodejs.org/dist/%s/%s' % (version, src_file)
    base_shell.work_on(session, work_dir)
    base_shell.wget(session, url)
    base_shell.run(session, 'tar xvzf ' + src_file)
    base_shell.run(session, 'cd ' + src_dir)
    base_shell.run(session, 'for dir in bin include lib share; do cp -par ${dir}/* /usr/local/${dir}/; done')
    base_shell.run(session, 'for dir in bin include lib share; do cp -par ${dir}/* /usr/${dir}/; done')

    session.su_exit()



