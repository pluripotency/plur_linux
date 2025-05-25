#!/usr/bin/env python3

import sys
import libvirt
from xml.dom import minidom


def msg_out(msg):
    sys.stdout.write(msg + '\n')


def get_dom_list(conn):
    dom_list = []
    for dom_id in conn.listDomainsID():
        dom_info = []
        vm = conn.lookupByID(dom_id)
        vm_xml_desc = minidom.parseString(vm.XMLDesc(0))
        for i, iface in enumerate(vm_xml_desc.getElementsByTagName("interface")):
            iface_type = iface.getAttribute("type")
            bridge = iface.getElementsByTagName("source")[0].getAttribute(iface_type)
            mac = iface.getElementsByTagName("mac")[0].getAttribute("address")
            device = iface.getElementsByTagName("target")[0].getAttribute("dev")
            virtualport = iface.getElementsByTagName("virtualport")
            if isinstance(virtualport, list) and len(virtualport) > 0:
                vport = virtualport[0].getAttribute("type")
            else:
                vport = ''
            dev_info = [vm.name(), device, mac, bridge, iface_type, vport]

            dom_info.append(dev_info)

        dom_list.append(dom_info)
    return dom_list


def show_taps(dom_list):
    msg_out("vm name      port   mac                source   type     virtualport")
    fmt = "%-12s %-6s %-18s %-8s %-8s %-8s"
    for dom_info in dom_list:
        for devInfo in dom_info:
            msg_out(fmt % (devInfo[0], devInfo[1], devInfo[2], devInfo[3], devInfo[4], devInfo[5]))


if __name__ == "__main__":
    conn = libvirt.openReadOnly("qemu:///system")
    dom_iist = get_dom_list(conn)
    show_taps(dom_iist)
