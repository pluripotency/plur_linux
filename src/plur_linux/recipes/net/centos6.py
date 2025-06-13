from plur import base_shell
from plur_linux.recipes.net import lldp, resolve_conf, persistentnet, ifcfg


def configure_sysconfig_network(hostname=None, gateway=None):
    def func(session):
        contents = [
            'NETWORKING=yes',
        ]
        if hostname is not None:
            contents += ['HOSTNAME=%s' % hostname]
        if gateway is not None:
            contents += ['GATEWAY=%s' % gateway]
        contents += ['NTPSERVERARGS=iburst']
        base_shell.here_doc(session, '/etc/sysconfig/network', contents)
    return func


def configure(session, current_node):
    persistentnet.create_rule(current_node)(session)

    base_shell.service_off(session, 'NetworkManager')

    hostname = None
    if hasattr(current_node, 'hostname'):
        hostname = current_node.hostname
    gateway = None
    if hasattr(current_node, 'gateway'):
        gateway = current_node.gateway
    configure_sysconfig_network(hostname, gateway)(session)

    search = None
    if hasattr(current_node, 'search'):
        search = current_node.search
    nameservers = None
    if hasattr(current_node, 'nameservers'):
        nameservers = current_node.nameservers
    resolve_conf.configure(nameservers, search)(session)

    if hasattr(current_node, 'ifaces'):
        for iface in current_node.ifaces:
            ifcfg.configure(iface)(session)

    lldp.configure(current_node)(session)
    base_shell.service_on(session, 'network')
