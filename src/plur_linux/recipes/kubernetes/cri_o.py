from mini import misc
from plur import session_wrap
from plur import base_shell


@session_wrap.sudo
def install_from_okd(session):
    # https://www.server-world.info/query?os=CentOS_Stream_9&p=kubernetes&f=2
    base_shell.run(session, misc.del_indent(r"""
    dnf install -y centos-release-okd-4.16
    sed -i -e "s/enabled=1/enabled=0/g" /etc/yum.repos.d/CentOS-OKD-4.16.repo
    dnf install --enablerepo=centos-okd-4.16 -y cri-o
    systemctl enable --now crio
    """))


@session_wrap.sudo
def install_from_crio_repo(session):
    # https://github.com/cri-o/packaging/blob/main/README.md
    base_shell.run(session, misc.del_indent(r"""
    CRIO_VERSION=v1.30
    """))
    base_shell.run(session, misc.del_indent(r"""
    cat <<EOF | tee /etc/yum.repos.d/cri-o.repo
    [cri-o]
    name=CRI-O
    baseurl=https://pkgs.k8s.io/addons:/cri-o:/stable:/$CRIO_VERSION/rpm/
    enabled=0
    gpgcheck=1
    gpgkey=https://pkgs.k8s.io/addons:/cri-o:/stable:/$CRIO_VERSION/rpm/repodata/repomd.xml.key
    EOF
    """))
    base_shell.run(session, misc.del_indent(r"""
    dnf install -y container-selinux
    dnf install -y --enablerepo=cri-o cri-o
    systemctl enable --now crio.service
    """))

