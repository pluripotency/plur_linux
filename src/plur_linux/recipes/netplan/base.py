from plur import session_wrap
from plur import base_shell
from plur_linux.recipes.netplan import base_str

## tested 26.04
def create_ipv4(ifname, ipv4_with_prefix, gw=None, nameservers=None, plan_name='50-ip.yaml'):
    @session_wrap.sudo
    def func(session):
        created_str = base_str.create_base_str(ifname)
        created_str += base_str.create_address_str(ipv4_with_prefix, gw, nameservers)
        base_shell.here_doc(session, f'/etc/netplan/{plan_name}', created_str.splitlines())
    return func

