from plur import base_shell
from plur_linux.recipes import firewalld
from . import common


def set_fw_control_plane(session):
    # firewalld.configure(ports=[
    #     '6443/tcp',
    #     '2379-2380/tcp',
    #     '10250/tcp',
    #     '10257/tcp',
    #     '10259/tcp',
    # ])(session)

    firewalld.configure(services=[
        'kube-control-plane',
        'kube-control-plane-secure',
        'kubelet',
        'kubelet-readonly',
    ], add=True)(session)


def set_fw_worker_node(session):
    firewalld.configure(ports=[
        '10250/tcp',
        '10256/tcp',
        '30000-32767/tcp',
    ])(session)


def setup_kubeadm_official(session):
    from plur_linux.recipes.ops import ops
    ops.permissive_selinux(session)

    from plur_linux.recipes.kubernetes import cri_o
    cri_o.install_from_crio_repo(session)
    common.install_base(session)
    common.configure_sysctl(session)
    common.configure_modules(session)
    common.prepare_kubenetes_official_repo(session)
    base_shell.run(session, 'sudo yum install --enablerepo=kubernetes -y kubelet kubeadm kubectl --disableexcludes=kubernetes')
    base_shell.run(session, 'sudo systemctl enable --now kubelet')


def setup_control_plane(host_lines, mgr_ip, ctl_ip, podnet='10.254.0.0/16'):
    def inner(session):
        common.create_hosts(host_lines)(session)
        set_fw_control_plane(session)
        setup_kubeadm_official(session)
        base_shell.run(session, common.create_kubeadm_init_sh_str(mgr_ip, ctl_ip, podnet))
    return inner



def setup_worker_node(host_lines):
    def inner(session):
        common.create_hosts(host_lines)(session)
        # set_fw_worker_node(session)
        setup_kubeadm_official(session)
    return inner
