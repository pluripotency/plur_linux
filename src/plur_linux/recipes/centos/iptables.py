import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
from string import Template


def runnable():
    return [
        setup_iptables
    ]


def setup_iptables(session, iptables):
    tcp = None
    udp = None
    if 'tcp' in iptables:
        tcp = iptables['tcp']
    if 'udp' in iptables:
        udp = iptables['udp']
    iptables_path = '/etc/sysconfig/iptables'
    shell.create_backup(session, iptables_path)
    shell.here_doc(session, iptables_path, create_iptables_contents(tcp, udp))
    shell.run(session, 'service iptables restart')


def create_iptables_contents(tcp, udp):
    """
    >>> import json
    >>> json.dumps(create_iptables_contents(), indent=2)
    """

    header = [
        "# Firewall configuration written by system-config-firewall",
        "# Manual customization of this file is not recommended.",
        "*filter",
        ":INPUT ACCEPT [0:0]",
        ":FORWARD ACCEPT [0:0]",
        ":OUTPUT ACCEPT [0:0]"
    ]
    header2 = [
        "-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
        "-A INPUT -p icmp -j ACCEPT",
        "-A INPUT -i lo -j ACCEPT"
    ]
    footer = [
        "-A INPUT -j REJECT --reject-with icmp-host-prohibited",
        "-A FORWARD -j REJECT --reject-with icmp-host-prohibited",
        "COMMIT"
    ]
    tcp_template = Template("-A INPUT -m state --state NEW -m tcp -p tcp --dport $tcp_port_number -j ACCEPT")
    udp_template = Template("-A INPUT -p udp --dport $udp_port_number -j ACCEPT")

    if isinstance(tcp, list):
        tcp_contents = [tcp_template.substitute(tcp_port_number=num) for num in tcp]
    else:
        tcp_contents = []
    if isinstance(udp, list):
        udp_contents = [udp_template.substitute(udp_port_number=num) for num in udp]
    else:
        udp_contents = []
    contents = header + header2 + tcp_contents + udp_contents + footer

    return contents

