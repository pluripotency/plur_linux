from mini import misc
from plur import session_wrap
from plur import base_shell
from recipes import firewalld
from . import common


# def prepare_kubenetes_repo(session):
#     version = 'v1.31'
#     base_shell.run(session, misc.del_indent(f"""
#     cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
#     [kubernetes]
#     name=Kubernetes
#     baseurl=https://pkgs.k8s.io/core:/stable:/{version}/rpm/
#     enabled=0
#     gpgcheck=1
#     gpgkey=https://pkgs.k8s.io/core:/stable:/{version}/rpm/repodata/repomd.xml.key
#     EOF
#
#     """))
#
#
# def configure_sysctl(session):
#     base_shell.run(session, misc.del_indent(f"""
#     cat <<EOF | sudo tee /etc/sysctl.d/99-k8s-cri.conf
#     net.bridge.bridge-nf-call-iptables=1
#     net.ipv4.ip_forward=1
#     net.bridge.bridge-nf-call-ip6tables=1
#     fs.inotify.max_user_watches = 524288
#     fs.inotify.max_user_instances = 512
#     EOF
#
#     """))
#     base_shell.run(session, 'sudo sysctl --system')
#
#
# @session_wrap.sudo
# def configure_modules(session):
#     base_shell.run(session, misc.del_indent(r"""
#     modprobe overlay
#     modprobe br_netfilter
#     echo -e overlay\\nbr_netfilter > /etc/modules-load.d/k8s.conf
#     """))
#
#
@session_wrap.sudo
def enable_epel_iptables(session):
    from plur.output_methods import success_f, send_line_f, waitprompt
    base_shell.run(session, misc.del_indent(r"""
    dnf install -y epel-release
    sed -i -e "s/enabled=1/enabled=0/g" /etc/yum.repos.d/epel.repo
    dnf install --enablerepo=epel -y iptables-legacy
    """))
    # session.do(base_shell.create_sequence('alternatives --config iptables', [
    #     ['Enter to keep the current.+type selection number:', send_line_f('')],
    #     [session.waitprompt, success_f(True)],
    # ]))
    # session.do(base_shell.create_sequence('alternatives --config iptables', [
    #     ['Enter to keep the current.+type selection number:', success_f(True)]
    # ]))
    # for line in session.child.before.split('\n'):
    #     if re.search('/usr/sbin/iptables-legacy', line):



@session_wrap.sudo
def setup_kubeadm(session):
    from recipes.ops import ops
    ops.permissive_selinux(session)

    from recipes.kubernetes import cri_o
    #cri_o.install_from_okd(session)
    cri_o.install_from_crio_repo(session)

    common.install_base(session)
    common.configure_sysctl(session)
    common.configure_modules(session)
    enable_epel_iptables(session)
    common.prepare_kubenetes_official_repo(session)
    base_shell.run(session, 'sudo yum install --enablerepo=kubernetes -y kubeadm kubelet cri-tools iproute-tc container-selinux --disableexcludes=kubernetes')
    base_shell.run(session, 'sudo systemctl enable --now kubelet')


def setup_control_plane(host_lines, mgr_ip='192.168.10.81', ctl_ip='192.168.10.82', podnet='10.255.0.0/16'):
    @session_wrap.sudo
    def inner(session):
        common.create_hosts(host_lines)(session)
        setup_kubeadm(session)
        firewalld.configure(services=[
            'kube-control-plane',
            'kube-control-plane-secure',
            'kubelet',
            'kubelet-readonly',
        ], ports=[
            '4244-4245/tcp',  # hubble
        ], add=True)(session)
        base_shell.run(session, common.create_kubeadm_init_sh_str(mgr_ip, ctl_ip, podnet))
    return inner


def setup_worker_node(host_lines):
    @session_wrap.sudo
    def inner(session):
        common.create_hosts(host_lines)(session)
        setup_kubeadm(session)
        base_shell.run(session, 'sudo systemctl disable --now firewalld')
    return inner
