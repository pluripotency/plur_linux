#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell
from plur import output_methods

success = output_methods.success
create_sequence = base_shell.create_sequence


def is_status_rxtx(session, iface):
    actions = 'lldptool -l -i %s adminStatus' % iface
    rows = [['adminStatus=rxtx', success, True, 'rxtx']]
    rows += [['adminStatus=disabled', success, False, 'disabled']]

    result = session.do(create_sequence(actions, rows))
    session.child.expect([session.waitprompt])

    return result


def enable_lldpad(session):
    if not base_shell.check_command_exists(session, 'lldptool'):
        base_shell.yum_install(session, {'packages': ['lldpad']})
        base_shell.service_on(session, 'lldpad')


def for_sh():
    """
    #! /bin/bash
    dnf install -y lldpad
    systemctl enable --now lldpad

    for IFACE in eno5 eno6 eno7 eno8 ens1f0 ens1f1 ens1f2 ens1f3
    do
    lldptool -i ${IFACE} set-lldp adminStatus=rxtx
    lldptool -i ${IFACE} set-tlv -V sysName enableTx=yes
    lldptool -i ${IFACE} set-tlv -V sysDesc enableTx=yes
    lldptool -i ${IFACE} set-tlv -V portDesc enableTx=yes
    done

    """


def configure_basic_settings_actions(iface_name):
    actions = [
        'lldptool -i %s set-lldp adminStatus=rxtx' % iface_name
        , 'lldptool -i %s set-tlv -V sysName enableTx=yes' % iface_name
        , 'lldptool -i %s set-tlv -V sysDesc enableTx=yes' % iface_name
        , 'lldptool -i %s set-tlv -V portDesc enableTx=yes' % iface_name
    ]
    return actions


def configure(node):
    def func(session):
        if hasattr(node, 'ifaces'):
            lldp_ifaces = []
            for iface in node.ifaces:
                if 'lldp' in iface and iface['lldp']:
                    iface_name = iface['name'] if 'name' in iface else iface['con_name']
                    lldp_ifaces += [iface_name]
            if len(lldp_ifaces) > 0:
                enable_lldpad(session)
                for iface_name in lldp_ifaces:
                    [base_shell.run(session, action) for action in configure_basic_settings_actions(iface_name)]
    return func

