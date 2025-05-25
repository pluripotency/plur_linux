
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell


def install(session):
    url = 'http://chrome.richardlloyd.org.uk/'
    installer = 'install_chrome.sh'

    shell.work_on(session, '~/Downloads/')
    shell.wget(session, url + installer)
    shell.run(session, 'chmod u+x ' + installer)

    # action = 'sudo ./%s' % installer
    # rows = [['\(y/n\) \?', shell.send_line, 'y', '']]
    # rows += [['', shell.waitprompt, '', '']]
    # session.do(shell.create_sequence(action, rows))

