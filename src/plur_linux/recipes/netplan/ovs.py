from plur import session_wrap
from plur import base_shell
from plur_linux.recipes.netplan import ovs_str

## tested 26.04
def create_ovs(ifname, brname, ipv4_with_prefix=None, gw=None, nameservers=None, plan_name='50-ovs.yaml'):
    @session_wrap.sudo
    def func(session):
        created_str = ovs_str.create_ovs_str(ifname, brname, ipv4_with_prefix, gw, nameservers)
        base_shell.here_doc(session, f'/etc/netplan/{plan_name}', created_str.splitlines())
    return func

