from mini import misc
from plur import base_shell
from plur import session_wrap
from recipes.ops import ops
from recipes.centos import chrony
from recipes import firewalld


@session_wrap.sudo
def a8base_just_update(session):
    ops.disable_ipv6(session)
    session.set_timeout(1800)
    base_shell.run(session, 'dnf update -y')
    # dnf clean all causes long time to init dnf operation
    # base_shell.run(session, 'dnf clean all')
    session.set_timeout()


@session_wrap.sudo
def a8base_update(session):
    a8base_just_update(session)
    if not base_shell.check_command_exists(session, 'tmux'):
        base_shell.run(session, 'dnf install -y ' + ' '.join([
            'vim'
            , 'tmux'
            , 'git'
            , 'bind-utils'
            , 'dstat'
            , 'glusterfs-fuse'
        ]))
        chrony.configure(session)
        firewalld.configure(services=['ssh'], add=True)
        ops.remove_cockpit(session)
    # dnf clean all causes long time to init dnf operation
    # base_shell.run(session, 'dnf clean all')


