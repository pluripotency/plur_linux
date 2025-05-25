from misc import misc
from plur import base_shell
from plur import session_wrap


@session_wrap.sudo
def install_from_rdo_archived(session):
    [base_shell.run(session, a) for a in misc.del_indent_lines("""
    dnf install -y https://repos.fedorapeople.org/repos/openstack/archived/openstack-yoga/rdo-release-yoga-1.el8.noarch.rpm
    dnf config-manager --set-enabled centos-rabbitmq-38 ceph-pacific openstack-yoga centos-nfv-openvswitch
    dnf install -y openvswitch libibverbs NetworkManager-ovs
    systemctl enable --now openvswitch
    """)]
    base_shell.run(session, 'ls | grep CentOS | xargs -I{} sed -i -e "s/enabled=1/enabled=0/g" {}')


def install_from_centos_release_openstack(version):
    @session_wrap.sudo
    def func(session):
        [base_shell.run(session, a) for a in misc.del_indent_lines(f"""
        dnf install -y centos-release-openstack-{version}
        dnf install -y openvswitch libibverbs NetworkManager-ovs
        systemctl enable --now openvswitch
        """)]
        base_shell.work_on(session, '/etc/yum.repos.d/')
        base_shell.run(session, 'ls | grep CentOS | xargs -I{} sed -i -e "s/enabled=1/enabled=0/g" {}')
    return func


dict_ovs = {
    'almalinux8': {
        # this doesn't work by EOL 2024/6
        'yoga': install_from_rdo_archived
    },
    'almalinux9': {
        'caracal': install_from_centos_release_openstack('caracal')
    },
}
