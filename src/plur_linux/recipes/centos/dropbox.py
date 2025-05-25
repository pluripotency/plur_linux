import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell


def runnable():
    return [
        setup_dropbox
    ]


def setup_dropbox(session):
    extract_files = 'cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -'
    shell.run(session, extract_files)

    # Need login
    run_daemon = '~/.dropbox-dist/dropboxd'
    shell.run(session, run_daemon)

    script = 'mkdir -p ~/bin && wget -O ~/bin/dropbox.py "https://www.dropbox.com/download?dl=packages/dropbox.py" && chmod +x ~/bin/dropbox.py'
    shell.run(session, script)

    start_dropbox = '~/bin/dropbox.py start'
    shell.run(session, start_dropbox)
    stop_lansync = '~/bin/dropbox.py lansync n'
    shell.run(session, stop_lansync)

