#! /usr/bin/env python
import re
from plur import base_shell
from plur import session_wrap
from plur import ansi_colors
from recipes.net import lldp, nmcli, centos6, nsswitch, ifcfg


def configure(current_node):
    @session_wrap.sudo
    def func(session):
        platform = current_node.platform
        print(ansi_colors.yellow('platform: ')+ansi_colors.cyan(platform))

        if platform == 'centos7':
            nsswitch.change_resolve_order(session)
            if hasattr(current_node, 'ifaces'):
                ifcfg.remove_current_ifcfg(session)
                iface_list = current_node.ifaces

                nm_required = False
                for iface in iface_list:
                    if 'nm_controlled' in iface and iface['nm_controlled']:
                        nm_required = True

                if nm_required:
                    nmcli.install_nm_if_not_installed(session)
                nmcli.remove_duped_entries(session, iface_list)

                for iface in iface_list:
                    if 'nm_controlled' in iface and iface['nm_controlled']:
                        nmcli.configure(session, iface)
                    else:
                        ifcfg.configure(iface)(session)
                lldp.configure(current_node)(session)
                base_shell.service_on(session, 'network')
        elif platform == 'centos6':
            centos6.configure(session, current_node)
        elif re.match(r'^(fedora|centos|almalinux|rocky|redhat).*', platform):
            if hasattr(current_node, 'ifaces'):
                iface_list = current_node.ifaces
                nmcli.remove_duped_entries(session, iface_list)
                for iface in iface_list:
                    nmcli.configure(session, iface)

    return func
