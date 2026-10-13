from mini import misc
from plur import base_shell
from plur import session_wrap
from plur_linux.recipes import firewalld

@session_wrap.sudo
def install_glusterfs(session):
    action_lines = misc.del_indent_lines("""
    dnf install -y epel-release
    dnf install -y centos-release-gluster11
    sed -i -e "s/enabled=1/enabled=0/g" /etc/yum.repos.d/CentOS-Gluster-11.repo
    dnf --enablerepo=centos-gluster11,epel,crb -y install glusterfs-server
    systemctl enable --now glusterd
    gluster --version
    """)
    _ = [base_shell.run(session, action) for action in action_lines]
    firewalld.configure(services=['glusterfs'], add=True)(session)
    base_shell.here_doc(session, '/etc/sysctl.d/fs_inotify.conf', [
        'fs.inotify.max_user_watches=1000000',
    ])
    base_shell.run(session, 'sysctl --system')


