import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
from plur_linux.recipes.source_install import base as src_base


def install(session, url, venv=None):
    if url:
        src_dir = 'scapy-2.1.0'
        src_file = 'scapy-latest.tar.gz'
        # src_url = 'http://www.secdev.org/projects/scapy/files/%s' % src_file
        src_url = url + src_file

        src_base.prepare_work_dir(session, src_dir, src_file, src_url)
        if venv:
            shell.run(session, 'source $HOME/.virtualenv/%s/bin/activate' % venv)
            shell.run(session, 'python setup.py install')
        else:
            shell.run(session, 'sudo ./setup.py install')

