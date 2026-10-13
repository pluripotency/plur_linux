import sys
import os
sys.path.append(os.pardir)
from plur import base_shell as shell


def configure(nameservers, search=None):
    def func(session):
        contents = []
        if search is not None:
            contents += ['search %s' % search]
        if isinstance(nameservers, list):
            for nameserver in nameservers:
                contents += ['nameserver %s' % nameserver]
        contents += ['options timeout:1 attempts:1']
        shell.here_doc(session, '/etc/resolv.conf', contents)
    return func

