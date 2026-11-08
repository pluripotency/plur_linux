from plur import session_wrap
from plur import base_shell
from mini import misc
from plur_linux.recipes.netplan import base_str
hier_space = base_str.hier_space

def configure_netplan(ifaces):
    @session_wrap.sudo
    def func(session):
        netplan_dir = '/etc/netplan'
        plan_name = '50-ip.yaml'
        netplan_str = base_str.create_renderer_str()
        netplan_str += hier_space(2, "ethernets:")
        for i, iface in enumerate(ifaces):
            base_shell.run(session, f"IFACE=`ip l | egrep ^{i + 2}: |" + " awk '{print $2}' | cut -d: -f1`")
            base_shell.run(session, "IFMAC=`ip -br l | egrep ^$IFACE | awk '{print $3}'`")
            netplan_str += misc.del_indent("""

                $IFACE:
                  match:
                    macaddress: $IFMAC
                  set-name: $IFACE

            """)
            if iface["ip"] == "dhcp":
                netplan_str += base_str.create_if_dhcp_str(True)
            else:
                netplan_str += base_str.create_if_dhcp_str(False)
                ip = iface["ip"]
                gw = iface["gateway"]
                nameservers = iface["nameservers"]
                netplan_str += '\n' + base_str.create_address_str(ip, gw, nameservers)
        base_shell.here_doc(session, f'{netplan_dir}/{plan_name}', netplan_str.splitlines(), eof="EOF")
        base_shell.run(session, f"rm -f {netplan_dir}/50-cloud-init.yaml")
        base_shell.run(session, f"chmod 600 {netplan_dir}/*")
        base_shell.run(session, "netplan apply")

    return func

